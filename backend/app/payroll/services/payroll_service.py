"""Payroll processing service."""
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Tuple
from uuid import UUID
from calendar import monthrange

from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.payroll.models.employee import Employee, EmploymentStatus, PayFrequency
from app.payroll.models.contract import EmployeeContract, CompensationType, OvertimeEligibility
from app.payroll.models.deduction import DeductionType, EmployeeDeduction, DeductionCategory
from app.payroll.models.payroll_run import (
    PayPeriod, PayPeriodStatus, PayrollRun, PayrollRunStatus,
    PayrollLine, PayrollLineDeduction
)
from app.core.exceptions import NotFoundError, ValidationError, BusinessRuleError


# US Tax rates for 2024/2025 (simplified)
SOCIAL_SECURITY_RATE = Decimal("0.062")
MEDICARE_RATE = Decimal("0.0145")
SOCIAL_SECURITY_WAGE_BASE = Decimal("168600")  # 2024


class PayrollService:
    """Service for payroll processing."""

    def __init__(self, db: Session, customer_id: UUID):
        self.db = db
        self.customer_id = customer_id

    # ==========================================
    # PAY PERIOD MANAGEMENT
    # ==========================================

    async def create_pay_period(
        self,
        frequency: str,
        start_date: date,
        end_date: date,
        pay_date: date
    ) -> PayPeriod:
        """Create a pay period."""
        # Calculate period number
        year = start_date.year
        count_query = select(func.count(PayPeriod.id)).where(
            PayPeriod.customer_id == self.customer_id,
            PayPeriod.period_year == year,
            PayPeriod.frequency == frequency
        )
        count = self.db.execute(count_query).scalar() or 0

        period = PayPeriod(
            customer_id=self.customer_id,
            period_number=count + 1,
            period_year=year,
            start_date=start_date,
            end_date=end_date,
            pay_date=pay_date,
            frequency=frequency,
        )

        self.db.add(period)
        self.db.commit()
        self.db.refresh(period)
        return period

    async def get_pay_periods(
        self,
        year: Optional[int] = None,
        frequency: Optional[str] = None,
        status: Optional[PayPeriodStatus] = None
    ) -> List[PayPeriod]:
        """Get pay periods."""
        query = select(PayPeriod).where(PayPeriod.customer_id == self.customer_id)

        if year:
            query = query.where(PayPeriod.period_year == year)
        if frequency:
            query = query.where(PayPeriod.frequency == frequency)
        if status:
            query = query.where(PayPeriod.status == status)

        query = query.order_by(PayPeriod.start_date.desc())
        result = self.db.execute(query)
        return result.scalars().all()

    # ==========================================
    # PAYROLL RUN
    # ==========================================

    async def create_payroll_run(
        self,
        pay_period_id: UUID,
        run_type: str = "regular",
        created_by: Optional[UUID] = None
    ) -> PayrollRun:
        """Create a new payroll run."""
        pay_period = await self._get_pay_period(pay_period_id)

        if pay_period.status == PayPeriodStatus.CLOSED:
            raise BusinessRuleError("Pay period is closed")

        # Generate run number
        count_query = select(func.count(PayrollRun.id)).where(
            PayrollRun.customer_id == self.customer_id
        )
        count = self.db.execute(count_query).scalar() or 0
        run_number = f"PR-{datetime.now().year}-{(count + 1):05d}"

        payroll_run = PayrollRun(
            customer_id=self.customer_id,
            pay_period_id=pay_period_id,
            run_number=run_number,
            run_type=run_type,
            created_by=created_by,
        )

        self.db.add(payroll_run)
        self.db.commit()
        self.db.refresh(payroll_run)

        return payroll_run

    async def calculate_payroll(self, run_id: UUID) -> PayrollRun:
        """Calculate payroll for all employees."""
        payroll_run = await self._get_payroll_run(run_id, include_lines=True)

        if payroll_run.status != PayrollRunStatus.DRAFT:
            raise BusinessRuleError("Payroll run is not in draft status")

        payroll_run.status = PayrollRunStatus.CALCULATING
        self.db.flush()

        pay_period = payroll_run.pay_period

        # Get all active employees with contracts
        employees = await self._get_payroll_eligible_employees(pay_period.frequency)

        total_gross = Decimal(0)
        total_deductions = Decimal(0)
        total_net = Decimal(0)
        total_employer_taxes = Decimal(0)
        total_employer_benefits = Decimal(0)

        for employee in employees:
            contract = employee.active_contract
            if not contract:
                continue

            # Create payroll line
            line = await self._calculate_employee_payroll(
                payroll_run, pay_period, employee, contract
            )

            total_gross += line.gross_pay
            total_deductions += line.total_deductions
            total_net += line.net_pay
            total_employer_taxes += (
                line.employer_social_security + line.employer_medicare +
                line.employer_futa + line.employer_suta
            )
            total_employer_benefits += line.employer_benefits

        # Update run totals
        payroll_run.total_gross_pay = total_gross
        payroll_run.total_deductions = total_deductions
        payroll_run.total_net_pay = total_net
        payroll_run.total_employer_taxes = total_employer_taxes
        payroll_run.total_employer_benefits = total_employer_benefits
        payroll_run.employee_count = len(payroll_run.payroll_lines)
        payroll_run.status = PayrollRunStatus.PENDING_APPROVAL
        payroll_run.calculated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(payroll_run)

        return payroll_run

    async def _calculate_employee_payroll(
        self,
        payroll_run: PayrollRun,
        pay_period: PayPeriod,
        employee: Employee,
        contract: EmployeeContract
    ) -> PayrollLine:
        """Calculate payroll for a single employee."""
        # Create payroll line
        line = PayrollLine(
            payroll_run_id=payroll_run.id,
            employee_id=employee.id,
            contract_id=contract.id,
            employee_number=employee.employee_number,
            employee_name=employee.full_name,
            regular_rate=contract.calculate_hourly_rate(),
        )

        # Calculate hours and pay
        if contract.compensation_type == CompensationType.SALARY:
            # Salary employees get period salary
            line.regular_hours = contract.standard_hours_per_week * self._get_weeks_in_period(pay_period)
            line.regular_pay = contract.period_salary
        else:
            # Hourly - assume standard hours for now
            # In real system, would pull from timesheet
            line.regular_hours = contract.standard_hours_per_week * self._get_weeks_in_period(pay_period)
            line.regular_pay = line.regular_hours * contract.hourly_rate

        # Calculate overtime (simplified)
        if contract.overtime_eligibility == OvertimeEligibility.NON_EXEMPT:
            line.overtime_rate = line.regular_rate * contract.overtime_rate_multiplier
            # Overtime hours would come from timesheet
            line.overtime_pay = line.overtime_hours * line.overtime_rate

        line.calculate_gross()

        # Calculate taxes
        await self._calculate_taxes(line, employee, contract)

        # Calculate other deductions
        await self._calculate_deductions(line, employee)

        # Calculate employer costs
        await self._calculate_employer_costs(line, employee)

        line.calculate_net()

        # Update YTD
        await self._update_ytd(line, employee)

        self.db.add(line)
        return line

    async def _calculate_taxes(
        self,
        line: PayrollLine,
        employee: Employee,
        contract: EmployeeContract
    ) -> None:
        """Calculate tax deductions."""
        gross = line.gross_pay

        # Social Security (6.2% up to wage base)
        ss_taxable = min(gross, SOCIAL_SECURITY_WAGE_BASE - line.ytd_social_security)
        line.social_security = (ss_taxable * SOCIAL_SECURITY_RATE).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Medicare (1.45%)
        line.medicare = (gross * MEDICARE_RATE).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Federal tax (simplified - use tax tables in real implementation)
        line.federal_tax = self._calculate_federal_tax(gross, employee)

        # State tax (simplified)
        line.state_tax = self._calculate_state_tax(gross, employee)

        # Add tax deductions to total
        line.total_deductions = (
            line.social_security + line.medicare +
            line.federal_tax + line.state_tax + line.local_tax
        )

    def _calculate_federal_tax(self, gross: Decimal, employee: Employee) -> Decimal:
        """Calculate federal income tax (simplified)."""
        # Simplified calculation - use IRS tax tables in production
        # This is just an approximation based on filing status
        annual_gross = gross * 26  # Assume biweekly

        if employee.federal_filing_status == "single":
            if annual_gross <= 11600:
                tax_rate = Decimal("0.10")
            elif annual_gross <= 47150:
                tax_rate = Decimal("0.12")
            elif annual_gross <= 100525:
                tax_rate = Decimal("0.22")
            else:
                tax_rate = Decimal("0.24")
        else:  # Married
            if annual_gross <= 23200:
                tax_rate = Decimal("0.10")
            elif annual_gross <= 94300:
                tax_rate = Decimal("0.12")
            elif annual_gross <= 201050:
                tax_rate = Decimal("0.22")
            else:
                tax_rate = Decimal("0.24")

        return (gross * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _calculate_state_tax(self, gross: Decimal, employee: Employee) -> Decimal:
        """Calculate state income tax (simplified)."""
        # Simplified - varies by state
        state_rate = Decimal("0.05")  # 5% default
        return (gross * state_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    async def _calculate_deductions(self, line: PayrollLine, employee: Employee) -> None:
        """Calculate non-tax deductions (401k, insurance, etc.)."""
        # Get employee deductions
        query = select(EmployeeDeduction).where(
            EmployeeDeduction.employee_id == employee.id,
            EmployeeDeduction.is_active == True
        )
        result = self.db.execute(query)
        employee_deductions = result.scalars().all()

        for emp_ded in employee_deductions:
            ded_type = self.db.get(DeductionType, emp_ded.deduction_type_id)
            if not ded_type or ded_type.category == DeductionCategory.TAX:
                continue  # Skip tax deductions, already calculated

            amount = emp_ded.amount or ded_type.default_amount or Decimal(0)
            if emp_ded.percentage or ded_type.default_percentage:
                pct = emp_ded.percentage or ded_type.default_percentage
                amount = (line.gross_pay * pct).quantize(Decimal("0.01"))

            # Check limits
            if ded_type.annual_limit:
                ytd = emp_ded.ytd_employee_amount
                if ytd + amount > ded_type.annual_limit:
                    amount = max(Decimal(0), ded_type.annual_limit - ytd)

            if amount > 0:
                line.total_deductions += amount

                # Track deduction detail
                ded_line = PayrollLineDeduction(
                    payroll_line_id=line.id,
                    deduction_type_id=ded_type.id,
                    deduction_code=ded_type.code,
                    deduction_name=ded_type.name,
                    category=ded_type.category.value,
                    employee_amount=amount,
                )

                # Employer match
                if ded_type.employer_match and ded_type.employer_match_percentage:
                    employer_amount = (line.gross_pay * ded_type.employer_match_percentage).quantize(Decimal("0.01"))
                    if ded_type.employer_match_limit:
                        employer_amount = min(employer_amount, ded_type.employer_match_limit)
                    ded_line.employer_amount = employer_amount

                self.db.add(ded_line)

    async def _calculate_employer_costs(self, line: PayrollLine, employee: Employee) -> None:
        """Calculate employer-side costs."""
        gross = line.gross_pay

        # Employer Social Security
        ss_taxable = min(gross, SOCIAL_SECURITY_WAGE_BASE - line.ytd_social_security)
        line.employer_social_security = (ss_taxable * SOCIAL_SECURITY_RATE).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Employer Medicare
        line.employer_medicare = (gross * MEDICARE_RATE).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # FUTA (Federal Unemployment - 6% on first $7000)
        futa_taxable = min(gross, Decimal("7000"))
        line.employer_futa = (futa_taxable * Decimal("0.006")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # SUTA (State Unemployment - varies by state)
        line.employer_suta = (gross * Decimal("0.027")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        line.total_employer_cost = (
            line.employer_social_security + line.employer_medicare +
            line.employer_futa + line.employer_suta + line.employer_benefits
        )

    async def _update_ytd(self, line: PayrollLine, employee: Employee) -> None:
        """Update YTD totals on the line."""
        # Get previous YTD from last payroll
        prev_line = self.db.execute(
            select(PayrollLine)
            .join(PayrollRun)
            .where(
                PayrollLine.employee_id == employee.id,
                PayrollRun.status == PayrollRunStatus.COMPLETED
            )
            .order_by(PayrollRun.completed_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        if prev_line:
            line.ytd_gross = prev_line.ytd_gross + line.gross_pay
            line.ytd_federal_tax = prev_line.ytd_federal_tax + line.federal_tax
            line.ytd_state_tax = prev_line.ytd_state_tax + line.state_tax
            line.ytd_social_security = prev_line.ytd_social_security + line.social_security
            line.ytd_medicare = prev_line.ytd_medicare + line.medicare
            line.ytd_net = prev_line.ytd_net + line.net_pay
        else:
            line.ytd_gross = line.gross_pay
            line.ytd_federal_tax = line.federal_tax
            line.ytd_state_tax = line.state_tax
            line.ytd_social_security = line.social_security
            line.ytd_medicare = line.medicare
            line.ytd_net = line.net_pay

    async def approve_payroll(self, run_id: UUID, user_id: UUID) -> PayrollRun:
        """Approve payroll run."""
        payroll_run = await self._get_payroll_run(run_id)

        if payroll_run.status != PayrollRunStatus.PENDING_APPROVAL:
            raise BusinessRuleError("Payroll run is not pending approval")

        payroll_run.status = PayrollRunStatus.APPROVED
        payroll_run.approved_by = user_id
        payroll_run.approved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(payroll_run)
        return payroll_run

    async def process_payments(self, run_id: UUID) -> PayrollRun:
        """Process payments for approved payroll."""
        payroll_run = await self._get_payroll_run(run_id, include_lines=True)

        if payroll_run.status != PayrollRunStatus.APPROVED:
            raise BusinessRuleError("Payroll must be approved before processing payments")

        payroll_run.status = PayrollRunStatus.PROCESSING_PAYMENTS
        self.db.flush()

        # Process each line
        for line in payroll_run.payroll_lines:
            # In real implementation, integrate with payment processor
            line.payment_status = "processed"

        payroll_run.status = PayrollRunStatus.COMPLETED
        payroll_run.completed_at = datetime.utcnow()

        # Close pay period
        payroll_run.pay_period.status = PayPeriodStatus.COMPLETED
        payroll_run.pay_period.total_gross = payroll_run.total_gross_pay
        payroll_run.pay_period.total_deductions = payroll_run.total_deductions
        payroll_run.pay_period.total_net = payroll_run.total_net_pay
        payroll_run.pay_period.employee_count = payroll_run.employee_count

        self.db.commit()
        self.db.refresh(payroll_run)
        return payroll_run

    async def get_payroll_runs(
        self,
        status: Optional[PayrollRunStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[PayrollRun], int]:
        """Get payroll runs."""
        query = select(PayrollRun).where(
            PayrollRun.customer_id == self.customer_id
        )

        if status:
            query = query.where(PayrollRun.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()

        query = query.order_by(PayrollRun.run_date.desc())
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        runs = result.scalars().all()

        return runs, total

    async def get_payroll_run_details(self, run_id: UUID) -> PayrollRun:
        """Get payroll run with lines."""
        query = select(PayrollRun).where(
            PayrollRun.id == run_id,
            PayrollRun.customer_id == self.customer_id
        ).options(selectinload(PayrollRun.payroll_lines))

        result = self.db.execute(query)
        payroll_run = result.scalar_one_or_none()

        if not payroll_run:
            raise NotFoundError(f"Payroll run not found: {run_id}")
        return payroll_run

    # ==========================================
    # HELPERS
    # ==========================================

    async def _get_payroll_eligible_employees(self, frequency: str) -> List[Employee]:
        """Get employees eligible for payroll."""
        query = select(Employee).where(
            Employee.customer_id == self.customer_id,
            Employee.employment_status == EmploymentStatus.ACTIVE,
            Employee.is_active == True
        ).options(selectinload(Employee.contracts))

        result = self.db.execute(query)
        employees = result.scalars().all()

        # Filter by pay frequency
        eligible = []
        for emp in employees:
            contract = emp.active_contract
            if contract and contract.pay_frequency.value == frequency:
                eligible.append(emp)

        return eligible

    def _get_weeks_in_period(self, pay_period: PayPeriod) -> Decimal:
        """Get number of weeks in a pay period."""
        if pay_period.frequency == "weekly":
            return Decimal("1")
        elif pay_period.frequency == "biweekly":
            return Decimal("2")
        elif pay_period.frequency == "semimonthly":
            return Decimal("2.166666")
        else:  # monthly
            return Decimal("4.333333")

    async def _get_pay_period(self, period_id: UUID) -> PayPeriod:
        """Get pay period by ID."""
        period = self.db.get(PayPeriod, period_id)
        if not period or period.customer_id != self.customer_id:
            raise NotFoundError(f"Pay period not found: {period_id}")
        return period

    async def _get_payroll_run(self, run_id: UUID, include_lines: bool = False) -> PayrollRun:
        """Get payroll run by ID."""
        if include_lines:
            query = select(PayrollRun).where(
                PayrollRun.id == run_id,
                PayrollRun.customer_id == self.customer_id
            ).options(selectinload(PayrollRun.payroll_lines))
            result = self.db.execute(query)
            run = result.scalar_one_or_none()
        else:
            run = self.db.get(PayrollRun, run_id)
            if run and run.customer_id != self.customer_id:
                run = None
        if not run:
            raise NotFoundError(f"Payroll run not found: {run_id}")
        return run
