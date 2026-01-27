"""Financial statement generation service."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.accounting.models import Account, AccountType, JournalEntry, JournalEntryLine
from app.reporting.schemas.financial_statements import (
    StatementLineItemData, BalanceSheetData, IncomeStatementData,
    CashFlowData, TrialBalanceLineData, TrialBalanceData
)


class FinancialStatementService:
    """Service for generating financial statements."""
    
    def __init__(self, db: Session, customer_id: UUID):
        self.db = db
        self.customer_id = customer_id
    
    # ==========================================
    # BALANCE SHEET
    # ==========================================
    
    async def generate_balance_sheet(
        self,
        as_of_date: date,
        compare_prior_period: bool = False,
        department_id: Optional[UUID] = None,
        show_zero_balances: bool = False
    ) -> BalanceSheetData:
        """Generate Balance Sheet."""
        company_name = await self._get_company_name()
        
        balances = await self._get_account_balances_as_of(as_of_date, department_id)
        
        prior_date = None
        prior_balances = {}
        if compare_prior_period:
            prior_date = date(as_of_date.year - 1, as_of_date.month, as_of_date.day)
            prior_balances = await self._get_account_balances_as_of(prior_date, department_id)
        
        current_assets = await self._build_section(
            balances, prior_balances, 
            [AccountType.ASSET], 
            account_filter=lambda a: a.code.startswith('1') and int(a.code[:2]) < 15,
            show_zero=show_zero_balances
        )
        total_current_assets = sum(line.current_period for line in current_assets)
        
        non_current_assets = await self._build_section(
            balances, prior_balances,
            [AccountType.ASSET],
            account_filter=lambda a: a.code.startswith('1') and int(a.code[:2]) >= 15,
            show_zero=show_zero_balances
        )
        total_non_current_assets = sum(line.current_period for line in non_current_assets)
        
        total_assets = total_current_assets + total_non_current_assets
        
        current_liabilities = await self._build_section(
            balances, prior_balances,
            [AccountType.LIABILITY],
            account_filter=lambda a: a.code.startswith('2') and int(a.code[:2]) < 25,
            show_zero=show_zero_balances,
            reverse_sign=True
        )
        total_current_liabilities = sum(line.current_period for line in current_liabilities)
        
        non_current_liabilities = await self._build_section(
            balances, prior_balances,
            [AccountType.LIABILITY],
            account_filter=lambda a: a.code.startswith('2') and int(a.code[:2]) >= 25,
            show_zero=show_zero_balances,
            reverse_sign=True
        )
        total_non_current_liabilities = sum(line.current_period for line in non_current_liabilities)
        
        total_liabilities = total_current_liabilities + total_non_current_liabilities
        
        equity = await self._build_section(
            balances, prior_balances,
            [AccountType.EQUITY],
            show_zero=show_zero_balances,
            reverse_sign=True
        )
        
        retained_earnings = await self._calculate_retained_earnings(as_of_date, department_id)
        equity.append(StatementLineItemData(
            code="RE",
            label="Retained Earnings (Current Year)",
            line_type="account",
            indent_level=1,
            current_period=retained_earnings,
            prior_period=None
        ))
        
        total_equity = sum(line.current_period for line in equity)
        total_liabilities_and_equity = total_liabilities + total_equity
        
        return BalanceSheetData(
            report_date=as_of_date,
            company_name=company_name,
            current_assets=current_assets,
            total_current_assets=total_current_assets,
            non_current_assets=non_current_assets,
            total_non_current_assets=total_non_current_assets,
            total_assets=total_assets,
            current_liabilities=current_liabilities,
            total_current_liabilities=total_current_liabilities,
            non_current_liabilities=non_current_liabilities,
            total_non_current_liabilities=total_non_current_liabilities,
            total_liabilities=total_liabilities,
            equity=equity,
            total_equity=total_equity,
            total_liabilities_and_equity=total_liabilities_and_equity,
            is_balanced=abs(total_assets - total_liabilities_and_equity) < Decimal("0.01"),
            prior_period_date=prior_date
        )
    
    # ==========================================
    # INCOME STATEMENT (P&L)
    # ==========================================
    
    async def generate_income_statement(
        self,
        start_date: date,
        end_date: date,
        compare_prior_period: bool = False,
        department_id: Optional[UUID] = None,
        show_zero_balances: bool = False
    ) -> IncomeStatementData:
        """Generate Income Statement (Profit & Loss)."""
        company_name = await self._get_company_name()
        
        balances = await self._get_period_balances(start_date, end_date, department_id)
        
        prior_balances = {}
        if compare_prior_period:
            days_diff = (end_date - start_date).days
            prior_end = start_date - timedelta(days=1)
            prior_start = prior_end - timedelta(days=days_diff)
            prior_balances = await self._get_period_balances(prior_start, prior_end, department_id)
        
        revenue = await self._build_section(
            balances, prior_balances,
            [AccountType.REVENUE],
            show_zero=show_zero_balances,
            reverse_sign=True
        )
        total_revenue = sum(line.current_period for line in revenue)
        
        cost_of_sales = await self._build_section(
            balances, prior_balances,
            [AccountType.EXPENSE],
            account_filter=lambda a: a.code.startswith('51'),
            show_zero=show_zero_balances
        )
        total_cost_of_sales = sum(line.current_period for line in cost_of_sales)
        
        gross_profit = total_revenue - total_cost_of_sales
        gross_margin = (gross_profit / total_revenue * 100) if total_revenue else None
        
        operating_expenses = await self._build_section(
            balances, prior_balances,
            [AccountType.EXPENSE],
            account_filter=lambda a: a.code.startswith('5') and not a.code.startswith('51'),
            show_zero=show_zero_balances
        )
        total_operating_expenses = sum(line.current_period for line in operating_expenses)
        
        operating_income = gross_profit - total_operating_expenses
        operating_margin = (operating_income / total_revenue * 100) if total_revenue else None
        
        other_income = await self._build_section(
            balances, prior_balances,
            [AccountType.REVENUE],
            account_filter=lambda a: a.code.startswith('6'),
            show_zero=show_zero_balances,
            reverse_sign=True
        )
        
        other_expenses = await self._build_section(
            balances, prior_balances,
            [AccountType.EXPENSE],
            account_filter=lambda a: a.code.startswith('7'),
            show_zero=show_zero_balances
        )
        
        total_other = sum(line.current_period for line in other_income) - \
                      sum(line.current_period for line in other_expenses)
        
        income_before_tax = operating_income + total_other
        tax_expense = Decimal(0)
        net_income = income_before_tax - tax_expense
        net_margin = (net_income / total_revenue * 100) if total_revenue else None
        
        return IncomeStatementData(
            period_start=start_date,
            period_end=end_date,
            company_name=company_name,
            revenue=revenue,
            total_revenue=total_revenue,
            cost_of_sales=cost_of_sales,
            total_cost_of_sales=total_cost_of_sales,
            gross_profit=gross_profit,
            gross_margin_percent=gross_margin,
            operating_expenses=operating_expenses,
            total_operating_expenses=total_operating_expenses,
            operating_income=operating_income,
            operating_margin_percent=operating_margin,
            other_income=other_income,
            other_expenses=other_expenses,
            total_other_income_expense=total_other,
            income_before_tax=income_before_tax,
            tax_expense=tax_expense,
            net_income=net_income,
            net_margin_percent=net_margin
        )
    
    # ==========================================
    # CASH FLOW STATEMENT
    # ==========================================
    
    async def generate_cash_flow(
        self,
        start_date: date,
        end_date: date,
        department_id: Optional[UUID] = None
    ) -> CashFlowData:
        """Generate Cash Flow Statement (Indirect Method)."""
        company_name = await self._get_company_name()
        
        income_statement = await self.generate_income_statement(
            start_date, end_date, department_id=department_id
        )
        
        operating = [
            StatementLineItemData(
                code="NI", label="Net Income", line_type="account",
                current_period=income_statement.net_income, bold=True
            )
        ]
        
        depreciation = await self._get_depreciation_expense(start_date, end_date, department_id)
        operating.append(StatementLineItemData(
            code="DEP", label="Depreciation & Amortization", line_type="account",
            indent_level=1, current_period=depreciation
        ))
        
        ar_change = await self._get_account_change("1200", start_date, end_date)
        operating.append(StatementLineItemData(
            code="AR", label="(Increase)/Decrease in Accounts Receivable", line_type="account",
            indent_level=1, current_period=-ar_change
        ))
        
        ap_change = await self._get_account_change("2100", start_date, end_date)
        operating.append(StatementLineItemData(
            code="AP", label="Increase/(Decrease) in Accounts Payable", line_type="account",
            indent_level=1, current_period=ap_change
        ))
        
        net_operating = sum(line.current_period for line in operating)
        
        investing = []
        ppe_change = await self._get_account_change("15", start_date, end_date, prefix=True)
        if ppe_change:
            investing.append(StatementLineItemData(
                code="PPE", label="Purchase of Property & Equipment", line_type="account",
                indent_level=1, current_period=-ppe_change
            ))
        net_investing = sum(line.current_period for line in investing)
        
        financing = []
        debt_change = await self._get_account_change("25", start_date, end_date, prefix=True)
        if debt_change:
            financing.append(StatementLineItemData(
                code="DEBT", label="Proceeds from/(Payments on) Long-term Debt", line_type="account",
                indent_level=1, current_period=debt_change
            ))
        net_financing = sum(line.current_period for line in financing)
        
        net_change = net_operating + net_investing + net_financing
        beginning_cash = await self._get_cash_balance(start_date - timedelta(days=1))
        ending_cash = beginning_cash + net_change
        
        return CashFlowData(
            period_start=start_date,
            period_end=end_date,
            company_name=company_name,
            operating_activities=operating,
            net_cash_from_operating=net_operating,
            investing_activities=investing,
            net_cash_from_investing=net_investing,
            financing_activities=financing,
            net_cash_from_financing=net_financing,
            net_change_in_cash=net_change,
            beginning_cash=beginning_cash,
            ending_cash=ending_cash
        )
    
    # ==========================================
    # TRIAL BALANCE
    # ==========================================
    
    async def generate_trial_balance(
        self,
        as_of_date: date,
        department_id: Optional[UUID] = None,
        show_zero_balances: bool = False
    ) -> TrialBalanceData:
        """Generate Trial Balance."""
        company_name = await self._get_company_name()
        
        balances = await self._get_account_balances_as_of(as_of_date, department_id)
        
        query = select(Account).where(
            Account.customer_id == self.customer_id,
            Account.is_active == True,
            Account.is_header == False
        ).order_by(Account.code)
        
        result = self.db.execute(query)
        accounts = result.scalars().all()
        
        lines = []
        total_debits = Decimal(0)
        total_credits = Decimal(0)
        
        for account in accounts:
            balance = balances.get(account.id, Decimal(0))
            
            if not show_zero_balances and balance == 0:
                continue
            
            debit = Decimal(0)
            credit = Decimal(0)
            
            if account.account_type in (AccountType.ASSET, AccountType.EXPENSE):
                if balance >= 0:
                    debit = balance
                else:
                    credit = abs(balance)
            else:
                if balance >= 0:
                    credit = balance
                else:
                    debit = abs(balance)
            
            lines.append(TrialBalanceLineData(
                account_code=account.code,
                account_name=account.name,
                account_type=account.account_type.value,
                debit=debit,
                credit=credit
            ))
            
            total_debits += debit
            total_credits += credit
        
        difference = total_debits - total_credits
        
        return TrialBalanceData(
            as_of_date=as_of_date,
            company_name=company_name,
            lines=lines,
            total_debits=total_debits,
            total_credits=total_credits,
            is_balanced=abs(difference) < Decimal("0.01"),
            difference=difference
        )
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    async def _get_company_name(self) -> str:
        """Get company name from customer."""
        return "Company Name"
    
    async def _get_account_balances_as_of(
        self,
        as_of_date: date,
        department_id: Optional[UUID] = None
    ) -> Dict[UUID, Decimal]:
        """Get account balances as of a specific date."""
        query = (
            select(
                JournalEntryLine.account_id,
                func.sum(JournalEntryLine.debit - JournalEntryLine.credit).label("balance")
            )
            .join(JournalEntry)
            .where(
                JournalEntry.customer_id == self.customer_id,
                JournalEntry.entry_date <= as_of_date,
                JournalEntry.status == "posted"
            )
            .group_by(JournalEntryLine.account_id)
        )
        
        if department_id:
            query = query.where(JournalEntryLine.department_id == department_id)
        
        result = self.db.execute(query)
        return {row.account_id: row.balance for row in result}
    
    async def _get_period_balances(
        self,
        start_date: date,
        end_date: date,
        department_id: Optional[UUID] = None
    ) -> Dict[UUID, Decimal]:
        """Get account activity for a period."""
        query = (
            select(
                JournalEntryLine.account_id,
                func.sum(JournalEntryLine.debit - JournalEntryLine.credit).label("balance")
            )
            .join(JournalEntry)
            .where(
                JournalEntry.customer_id == self.customer_id,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date,
                JournalEntry.status == "posted"
            )
            .group_by(JournalEntryLine.account_id)
        )
        
        if department_id:
            query = query.where(JournalEntryLine.department_id == department_id)
        
        result = self.db.execute(query)
        return {row.account_id: row.balance for row in result}
    
    async def _build_section(
        self,
        balances: Dict[UUID, Decimal],
        prior_balances: Dict[UUID, Decimal],
        account_types: List[AccountType],
        account_filter=None,
        show_zero: bool = False,
        reverse_sign: bool = False
    ) -> List[StatementLineItemData]:
        """Build a statement section from account balances."""
        query = select(Account).where(
            Account.customer_id == self.customer_id,
            Account.account_type.in_(account_types),
            Account.is_active == True,
            Account.is_header == False
        ).order_by(Account.code)
        
        result = self.db.execute(query)
        accounts = result.scalars().all()
        
        lines = []
        for account in accounts:
            if account_filter and not account_filter(account):
                continue
            
            balance = balances.get(account.id, Decimal(0))
            prior_balance = prior_balances.get(account.id)
            
            if not show_zero and balance == 0 and (prior_balance is None or prior_balance == 0):
                continue
            
            if reverse_sign:
                balance = -balance
                if prior_balance is not None:
                    prior_balance = -prior_balance
            
            variance = None
            variance_pct = None
            if prior_balance is not None:
                variance = balance - prior_balance
                if prior_balance != 0:
                    variance_pct = (variance / abs(prior_balance)) * 100
            
            lines.append(StatementLineItemData(
                code=account.code,
                label=account.name,
                line_type="account",
                indent_level=1,
                current_period=balance,
                prior_period=prior_balance,
                variance=variance,
                variance_percent=variance_pct
            ))
        
        return lines
    
    async def _calculate_retained_earnings(
        self,
        as_of_date: date,
        department_id: Optional[UUID] = None
    ) -> Decimal:
        """Calculate retained earnings (current year P&L)."""
        year_start = date(as_of_date.year, 1, 1)
        
        query = (
            select(
                func.sum(JournalEntryLine.credit - JournalEntryLine.debit).label("net_income")
            )
            .join(JournalEntry)
            .join(Account)
            .where(
                JournalEntry.customer_id == self.customer_id,
                JournalEntry.entry_date >= year_start,
                JournalEntry.entry_date <= as_of_date,
                JournalEntry.status == "posted",
                Account.account_type.in_([AccountType.REVENUE, AccountType.EXPENSE])
            )
        )
        
        if department_id:
            query = query.where(JournalEntryLine.department_id == department_id)
        
        result = self.db.execute(query)
        row = result.first()
        return row.net_income if row and row.net_income else Decimal(0)
    
    async def _get_depreciation_expense(
        self,
        start_date: date,
        end_date: date,
        department_id: Optional[UUID] = None
    ) -> Decimal:
        """Get depreciation expense for period."""
        query = (
            select(func.sum(JournalEntryLine.debit).label("depreciation"))
            .join(JournalEntry)
            .join(Account)
            .where(
                JournalEntry.customer_id == self.customer_id,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date,
                JournalEntry.status == "posted",
                Account.code.like("53%")
            )
        )
        
        result = self.db.execute(query)
        row = result.first()
        return row.depreciation if row and row.depreciation else Decimal(0)
    
    async def _get_account_change(
        self,
        account_code: str,
        start_date: date,
        end_date: date,
        prefix: bool = False
    ) -> Decimal:
        """Get change in account balance over period."""
        end_balance = await self._get_account_balance_by_code(account_code, end_date, prefix)
        start_balance = await self._get_account_balance_by_code(
            account_code, start_date - timedelta(days=1), prefix
        )
        return end_balance - start_balance
    
    async def _get_account_balance_by_code(
        self,
        account_code: str,
        as_of_date: date,
        prefix: bool = False
    ) -> Decimal:
        """Get account balance by code."""
        query = (
            select(func.sum(JournalEntryLine.debit - JournalEntryLine.credit).label("balance"))
            .join(JournalEntry)
            .join(Account)
            .where(
                JournalEntry.customer_id == self.customer_id,
                JournalEntry.entry_date <= as_of_date,
                JournalEntry.status == "posted"
            )
        )
        
        if prefix:
            query = query.where(Account.code.like(f"{account_code}%"))
        else:
            query = query.where(Account.code == account_code)
        
        result = self.db.execute(query)
        row = result.first()
        return row.balance if row and row.balance else Decimal(0)
    
    async def _get_cash_balance(self, as_of_date: date) -> Decimal:
        """Get total cash balance."""
        return await self._get_account_balance_by_code("1000", as_of_date, prefix=True)
