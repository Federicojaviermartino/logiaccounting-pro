"""Employee management service."""
from datetime import datetime, date
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.payroll.models.employee import Employee, EmploymentStatus, EmploymentType
from app.payroll.models.contract import EmployeeContract
from app.payroll.schemas.employee import EmployeeCreate, EmployeeUpdate, TaxInfoUpdate, TerminateEmployee
from app.payroll.schemas.contract import ContractCreate, ContractUpdate
from app.core.exceptions import NotFoundError, ValidationError, BusinessRuleError


class EmployeeService:
    """Service for employee operations."""

    EMPLOYEE_UPDATABLE_FIELDS = frozenset({
        "first_name", "last_name", "email", "phone", "date_of_birth",
        "gender", "address", "city", "state", "postal_code", "country",
        "employment_status", "employment_type", "department_id",
        "job_title", "manager_id", "hire_date",
    })

    TAX_UPDATABLE_FIELDS = frozenset({
        "tax_id", "filing_status", "federal_allowances",
        "state_allowances", "additional_withholding",
    })

    def __init__(self, db: Session, customer_id: UUID):
        self.db = db
        self.customer_id = customer_id

    # ==========================================
    # EMPLOYEE CRUD
    # ==========================================

    async def create_employee(self, data: EmployeeCreate, created_by: Optional[UUID] = None) -> Employee:
        """Create new employee."""
        # Generate employee number
        employee_number = await self._generate_employee_number()

        # Check email uniqueness
        existing = self.db.execute(
            select(Employee).where(
                Employee.customer_id == self.customer_id,
                Employee.email == data.email
            )
        ).scalar_one_or_none()

        if existing:
            raise ValidationError(f"Employee with email {data.email} already exists")

        employee = Employee(
            customer_id=self.customer_id,
            employee_number=employee_number,
            employment_status=EmploymentStatus.ACTIVE,
            employment_type=EmploymentType(data.employment_type),
            **data.model_dump(exclude={"employment_type"})
        )

        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)

        return employee

    async def update_employee(self, employee_id: UUID, data: EmployeeUpdate) -> Employee:
        """Update employee."""
        employee = await self.get_employee_by_id(employee_id)

        update_data = data.model_dump(exclude_unset=True)

        # Handle enum conversion
        if "employment_status" in update_data and update_data["employment_status"]:
            update_data["employment_status"] = EmploymentStatus(update_data["employment_status"])
        if "employment_type" in update_data and update_data["employment_type"]:
            update_data["employment_type"] = EmploymentType(update_data["employment_type"])

        for key, value in update_data.items():
            if key in self.EMPLOYEE_UPDATABLE_FIELDS:
                setattr(employee, key, value)

        self.db.commit()
        self.db.refresh(employee)
        return employee

    async def update_tax_info(self, employee_id: UUID, data: TaxInfoUpdate) -> Employee:
        """Update employee tax information."""
        employee = await self.get_employee_by_id(employee_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key in self.TAX_UPDATABLE_FIELDS:
                setattr(employee, key, value)

        self.db.commit()
        self.db.refresh(employee)
        return employee

    async def terminate_employee(self, employee_id: UUID, data: TerminateEmployee) -> Employee:
        """Terminate employee."""
        employee = await self.get_employee_by_id(employee_id, include_contracts=True)

        if employee.employment_status == EmploymentStatus.TERMINATED:
            raise BusinessRuleError("Employee is already terminated")

        employee.employment_status = EmploymentStatus.TERMINATED
        employee.termination_date = data.termination_date
        employee.termination_reason = data.termination_reason
        employee.is_active = False

        # Deactivate contracts
        for contract in employee.contracts:
            if contract.is_active:
                contract.is_active = False
                contract.end_date = data.termination_date

        self.db.commit()
        self.db.refresh(employee)
        return employee

    async def get_employee_by_id(self, employee_id: UUID, include_contracts: bool = False) -> Employee:
        """Get employee by ID."""
        query = select(Employee).where(
            Employee.id == employee_id,
            Employee.customer_id == self.customer_id
        )

        if include_contracts:
            query = query.options(selectinload(Employee.contracts))

        result = self.db.execute(query)
        employee = result.scalar_one_or_none()

        if not employee:
            raise NotFoundError(f"Employee not found: {employee_id}")
        return employee

    async def get_employees(
        self,
        status: Optional[EmploymentStatus] = None,
        department_id: Optional[UUID] = None,
        employment_type: Optional[EmploymentType] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Employee], int]:
        """Get employees with filtering."""
        query = select(Employee).where(Employee.customer_id == self.customer_id)

        if status:
            query = query.where(Employee.employment_status == status)
        if department_id:
            query = query.where(Employee.department_id == department_id)
        if employment_type:
            query = query.where(Employee.employment_type == employment_type)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Employee.first_name.ilike(search_term)) |
                (Employee.last_name.ilike(search_term)) |
                (Employee.email.ilike(search_term)) |
                (Employee.employee_number.ilike(search_term))
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()

        query = query.order_by(Employee.last_name, Employee.first_name)
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        employees = result.scalars().all()

        return employees, total

    async def get_active_employees(self) -> List[Employee]:
        """Get all active employees."""
        query = select(Employee).where(
            Employee.customer_id == self.customer_id,
            Employee.employment_status == EmploymentStatus.ACTIVE,
            Employee.is_active == True
        ).options(selectinload(Employee.contracts))

        result = self.db.execute(query)
        return result.scalars().all()

    # ==========================================
    # CONTRACT MANAGEMENT
    # ==========================================

    async def create_contract(self, employee_id: UUID, data: ContractCreate) -> EmployeeContract:
        """Create employee contract."""
        employee = await self.get_employee_by_id(employee_id, include_contracts=True)

        # Generate contract number
        count = len(employee.contracts) if employee.contracts else 0
        contract_number = f"{employee.employee_number}-C{(count + 1):02d}"

        # Deactivate previous contracts
        for contract in employee.contracts:
            if contract.is_active and contract.end_date is None:
                contract.end_date = data.start_date
                contract.is_active = False

        contract = EmployeeContract(
            employee_id=employee_id,
            contract_number=contract_number,
            **data.model_dump()
        )

        self.db.add(contract)

        # Update employee job title
        employee.job_title = data.job_title
        if data.department_id:
            employee.department_id = data.department_id

        self.db.commit()
        self.db.refresh(contract)
        return contract

    async def update_contract(self, contract_id: UUID, data: ContractUpdate) -> EmployeeContract:
        """Update contract."""
        contract = await self._get_contract(contract_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(contract, key):
                setattr(contract, key, value)

        self.db.commit()
        self.db.refresh(contract)
        return contract

    async def get_employee_contracts(self, employee_id: UUID) -> List[EmployeeContract]:
        """Get all contracts for an employee."""
        query = select(EmployeeContract).where(
            EmployeeContract.employee_id == employee_id
        ).order_by(EmployeeContract.start_date.desc())

        result = self.db.execute(query)
        return result.scalars().all()

    async def _get_contract(self, contract_id: UUID) -> EmployeeContract:
        """Get contract by ID."""
        contract = self.db.get(EmployeeContract, contract_id)
        if not contract:
            raise NotFoundError(f"Contract not found: {contract_id}")
        return contract

    async def _generate_employee_number(self) -> str:
        """Generate unique employee number."""
        year = datetime.now().year
        count_query = select(func.count(Employee.id)).where(
            Employee.customer_id == self.customer_id
        )
        count = self.db.execute(count_query).scalar() or 0
        return f"EMP-{year}-{(count + 1):04d}"
