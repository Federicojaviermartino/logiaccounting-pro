"""API routes for deductions and benefits."""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_permissions
from app.auth.models import User
from app.payroll.models.deduction import DeductionType, EmployeeDeduction, BenefitType
from app.payroll.schemas.deduction import (
    DeductionTypeCreate, DeductionTypeUpdate, DeductionTypeResponse,
    EmployeeDeductionCreate, EmployeeDeductionUpdate, EmployeeDeductionResponse,
    BenefitTypeCreate, BenefitTypeResponse
)
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/deductions", tags=["Deductions & Benefits"])


# ==========================================
# DEDUCTION TYPES
# ==========================================

@router.get("/types", response_model=List[DeductionTypeResponse])
async def get_deduction_types(
    category: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get deduction types."""
    query = select(DeductionType).where(
        DeductionType.customer_id == current_user.customer_id
    )
    if category:
        query = query.where(DeductionType.category == category)
    if active_only:
        query = query.where(DeductionType.is_active == True)

    query = query.order_by(DeductionType.sort_order, DeductionType.code)
    result = db.execute(query)
    return result.scalars().all()


@router.post("/types", response_model=DeductionTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_deduction_type(
    data: DeductionTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["payroll.manage"]))
):
    """Create deduction type."""
    ded_type = DeductionType(
        customer_id=current_user.customer_id,
        **data.model_dump()
    )
    db.add(ded_type)
    db.commit()
    db.refresh(ded_type)
    return ded_type


@router.put("/types/{type_id}", response_model=DeductionTypeResponse)
async def update_deduction_type(
    type_id: UUID,
    data: DeductionTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["payroll.manage"]))
):
    """Update deduction type."""
    ded_type = db.get(DeductionType, type_id)
    if not ded_type or ded_type.customer_id != current_user.customer_id:
        raise NotFoundError(f"Deduction type not found: {type_id}")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ded_type, key, value)

    db.commit()
    db.refresh(ded_type)
    return ded_type


# ==========================================
# EMPLOYEE DEDUCTIONS
# ==========================================

@router.get("/employee/{employee_id}", response_model=List[EmployeeDeductionResponse])
async def get_employee_deductions(
    employee_id: UUID,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get deductions assigned to an employee."""
    query = select(EmployeeDeduction).where(
        EmployeeDeduction.employee_id == employee_id
    )
    if active_only:
        query = query.where(EmployeeDeduction.is_active == True)

    result = db.execute(query)
    return result.scalars().all()


@router.post("/employee/{employee_id}", response_model=EmployeeDeductionResponse, status_code=status.HTTP_201_CREATED)
async def assign_deduction_to_employee(
    employee_id: UUID,
    data: EmployeeDeductionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["employees.edit"]))
):
    """Assign deduction to employee."""
    emp_ded = EmployeeDeduction(
        employee_id=employee_id,
        **data.model_dump()
    )
    db.add(emp_ded)
    db.commit()
    db.refresh(emp_ded)
    return emp_ded


@router.put("/employee-deduction/{deduction_id}", response_model=EmployeeDeductionResponse)
async def update_employee_deduction(
    deduction_id: UUID,
    data: EmployeeDeductionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["employees.edit"]))
):
    """Update employee deduction."""
    emp_ded = db.get(EmployeeDeduction, deduction_id)
    if not emp_ded:
        raise NotFoundError(f"Employee deduction not found: {deduction_id}")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(emp_ded, key, value)

    db.commit()
    db.refresh(emp_ded)
    return emp_ded


# ==========================================
# BENEFIT TYPES
# ==========================================

@router.get("/benefits/types", response_model=List[BenefitTypeResponse])
async def get_benefit_types(
    category: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get benefit types."""
    query = select(BenefitType).where(
        BenefitType.customer_id == current_user.customer_id
    )
    if category:
        query = query.where(BenefitType.category == category)
    if active_only:
        query = query.where(BenefitType.is_active == True)

    result = db.execute(query)
    return result.scalars().all()


@router.post("/benefits/types", response_model=BenefitTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_benefit_type(
    data: BenefitTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["payroll.manage"]))
):
    """Create benefit type."""
    benefit = BenefitType(
        customer_id=current_user.customer_id,
        **data.model_dump()
    )
    db.add(benefit)
    db.commit()
    db.refresh(benefit)
    return benefit
