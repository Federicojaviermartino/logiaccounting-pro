"""
Chart of Accounts API Routes
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User

from app.accounting.chart_of_accounts import (
    ChartOfAccountsService,
    AccountTreeBuilder,
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    AccountFilter,
    AccountTreeNode,
    AccountTypeResponse,
    get_template,
    get_available_templates,
)

router = APIRouter(prefix="/accounts", tags=["Chart of Accounts"])


@router.get("/types", response_model=List[AccountTypeResponse])
async def get_account_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all account types."""
    service = ChartOfAccountsService(db)
    types = service.get_account_types()
    return [t.to_dict() for t in types]


@router.get("/templates")
async def list_account_templates(
    current_user: User = Depends(get_current_user),
):
    """Get available chart of accounts templates."""
    return get_available_templates()


@router.post("/import-template")
async def import_account_template(
    template_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import a predefined chart of accounts template."""
    template = get_template(template_name)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    service = ChartOfAccountsService(db)

    from app.accounting.chart_of_accounts.schemas import AccountImportRow, AccountTypeEnum

    accounts = [
        AccountImportRow(
            code=a["code"],
            name=a["name"],
            type=AccountTypeEnum(a["type"].value),
            parent_code=a.get("parent_code"),
            is_header=a.get("is_header", False),
        )
        for a in template["accounts"]
    ]

    result = service.import_accounts(
        customer_id=current_user.customer_id,
        accounts=accounts,
        created_by=current_user.id,
    )

    return result


@router.get("/tree", response_model=List[AccountTreeNode])
async def get_account_tree(
    root_type: Optional[str] = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get hierarchical account tree."""
    builder = AccountTreeBuilder(db)
    return builder.build_tree(
        customer_id=current_user.customer_id,
        include_balances=True,
        include_inactive=include_inactive,
    )


@router.get("", response_model=dict)
async def list_accounts(
    search: Optional[str] = None,
    account_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_header: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List accounts with filtering."""
    service = ChartOfAccountsService(db)

    filters = AccountFilter(
        search=search,
        account_type=account_type,
        is_active=is_active,
        is_header=is_header,
    )

    accounts, total = service.get_accounts(
        customer_id=current_user.customer_id,
        filters=filters,
        page=page,
        page_size=page_size,
    )

    return {
        "accounts": [a.to_dict() for a in accounts],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new account."""
    service = ChartOfAccountsService(db)

    try:
        account = service.create_account(
            customer_id=current_user.customer_id,
            data=data,
            created_by=current_user.id,
        )
        return account.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get account details."""
    service = ChartOfAccountsService(db)
    account = service.get_account_by_id(account_id)

    if not account or account.customer_id != current_user.customer_id:
        raise HTTPException(status_code=404, detail="Account not found")

    return account.to_dict()


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: UUID,
    data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an account."""
    service = ChartOfAccountsService(db)

    account = service.get_account_by_id(account_id)
    if not account or account.customer_id != current_user.customer_id:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        account = service.update_account(account_id, data)
        return account.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{account_id}")
async def deactivate_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deactivate an account."""
    service = ChartOfAccountsService(db)

    account = service.get_account_by_id(account_id)
    if not account or account.customer_id != current_user.customer_id:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        service.deactivate_account(account_id)
        return {"message": "Account deactivated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{account_id}/balance")
async def get_account_balance(
    account_id: UUID,
    as_of_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get account balance."""
    from datetime import date

    service = ChartOfAccountsService(db)

    account = service.get_account_by_id(account_id)
    if not account or account.customer_id != current_user.customer_id:
        raise HTTPException(status_code=404, detail="Account not found")

    as_of = date.fromisoformat(as_of_date) if as_of_date else None

    return {
        "account_id": str(account_id),
        "balance": float(account.current_balance),
        "as_of_date": as_of.isoformat() if as_of else date.today().isoformat(),
    }
