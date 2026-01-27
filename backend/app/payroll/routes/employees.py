"""API routes for employee management."""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_permissions
from app.auth.models import User
from app.payroll.services.employee_service import EmployeeService
from app.payroll.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeSummary,
    TaxInfoUpdate, BankInfoUpdate, EmergencyContactUpdate, TerminateEmployee
)
from app.payroll.schemas.contract import ContractCreate, ContractUpdate, ContractResponse

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_model=dict)
async def get_employees(
    status: Optional[str] = None,
    department_id: Optional[UUID] = None,
    employment_type: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get employees with filtering."""
    service = EmployeeService(db, current_user.customer_id)
    employees, total = await service.get_employees(
        status=status, department_id=department_id,
        employment_type=employment_type, search=search,
        skip=skip, limit=limit
    )
    return {
        "items": [EmployeeSummary.model_validate(e) for e in employees],
        "total": total, "skip": skip, "limit": limit
    }


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get employee by ID."""
    service = EmployeeService(db, current_user.customer_id)
    return await service.get_employee_by_id(employee_id)


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["employees.create"]))
):
    """Create new employee."""
    service = EmployeeService(db, current_user.customer_id)
    return await service.create_employee(data, current_user.id)


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["employees.edit"]))
):
    """Update employee."""
    service = EmployeeService(db, current_user.customer_id)
    return await service.update_employee(employee_id, data)


@router.put("/{employee_id}/tax-info", response_model=EmployeeResponse)
async def update_tax_info(
    employee_id: UUID,
    data: TaxInfoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["employees.edit"]))
):
    """Update employee tax information."""
    service = EmployeeService(db, current_user.customer_id)
    return await service.update_tax_info(employee_id, data)


@router.post("/{employee_id}/terminate", response_model=EmployeeResponse)
async def terminate_employee(
    employee_id: UUID,
    data: TerminateEmployee,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["employees.terminate"]))
):
    """Terminate employee."""
    service = EmployeeService(db, current_user.customer_id)
    return await service.terminate_employee(employee_id, data)


# ==========================================
# CONTRACTS
# ==========================================

@router.get("/{employee_id}/contracts", response_model=List[ContractResponse])
async def get_employee_contracts(
    employee_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get employee contracts."""
    service = EmployeeService(db, current_user.customer_id)
    return await service.get_employee_contracts(employee_id)


@router.post("/{employee_id}/contracts", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    employee_id: UUID,
    data: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["employees.edit"]))
):
    """Create employee contract."""
    service = EmployeeService(db, current_user.customer_id)
    return await service.create_contract(employee_id, data)


@router.put("/contracts/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: UUID,
    data: ContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["employees.edit"]))
):
    """Update contract."""
    service = EmployeeService(db, current_user.customer_id)
    return await service.update_contract(contract_id, data)
