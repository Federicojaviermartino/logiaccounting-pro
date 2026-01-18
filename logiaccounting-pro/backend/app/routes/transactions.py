"""
Transactions routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.models.store import db
from app.utils.auth import get_current_user, require_roles
from app.schemas.schemas import TransactionCreate, TransactionUpdate

router = APIRouter()


@router.get("")
async def get_transactions(
    type: Optional[str] = None,
    category_id: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """Get all transactions"""
    filters = {k: v for k, v in {"type": type, "category_id": category_id, "project_id": project_id}.items() if v}
    
    if current_user["role"] == "supplier":
        filters["supplier_id"] = current_user["id"]
    elif current_user["role"] == "client":
        filters["client_id"] = current_user["id"]
    
    transactions = db.transactions.find_all(filters if filters else None)
    transactions = sorted(transactions, key=lambda x: x.get("date", x["created_at"]), reverse=True)
    
    for t in transactions:
        cat = db.categories.find_by_id(t.get("category_id"))
        proj = db.projects.find_by_id(t.get("project_id"))
        t["category_name"] = cat["name"] if cat else None
        t["project_code"] = proj["code"] if proj else None
    
    return {"transactions": transactions[:limit]}


@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific transaction"""
    transaction = db.transactions.find_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_transaction(
    request: TransactionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new transaction"""
    data = request.model_dump()
    data["created_by"] = current_user["id"]
    
    if current_user["role"] == "supplier":
        data["supplier_id"] = current_user["id"]
    elif current_user["role"] == "client":
        data["client_id"] = current_user["id"]
    
    transaction = db.transactions.create(data)
    
    if current_user["role"] != "admin":
        db.notifications.create({
            "type": "transaction",
            "title": "New Transaction",
            "message": f"{'Income' if request.type == 'income' else 'Expense'} of ${request.amount:.2f} recorded",
            "target_role": "admin",
            "related_id": transaction["id"],
            "related_type": "transaction",
            "read": False
        })
    
    return transaction


@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    request: TransactionUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a transaction"""
    transaction = db.transactions.find_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    
    if current_user["role"] != "admin" and transaction.get("created_by") != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    return db.transactions.update(transaction_id, update_data)


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a transaction (admin only)"""
    if not db.transactions.delete(transaction_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return {"success": True}
