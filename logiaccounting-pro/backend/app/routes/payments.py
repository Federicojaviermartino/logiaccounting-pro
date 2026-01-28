"""
Payments routes with cross-role notifications
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.store import db
from app.utils.auth import get_current_user, require_roles
from app.utils.datetime_utils import utc_now
from app.schemas.schemas import PaymentCreate, PaymentUpdate, PaymentMarkPaid

router = APIRouter()


@router.get("")
async def get_payments(
    payment_status: Optional[str] = None,
    type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all payments"""
    filters = {}
    
    if payment_status:
        filters["status"] = payment_status
    if type:
        filters["type"] = type
    
    if current_user["role"] == "supplier":
        filters["supplier_id"] = current_user["id"]
    elif current_user["role"] == "client":
        filters["client_id"] = current_user["id"]
    
    payments = db.payments.find_all(filters if filters else None)
    now = utc_now()
    
    for p in payments:
        supplier = db.users.find_by_id(p.get("supplier_id"))
        client = db.users.find_by_id(p.get("client_id"))
        p["supplier_name"] = supplier.get("company_name") if supplier else None
        p["client_name"] = client.get("company_name") if client else None
        
        try:
            due_date = datetime.fromisoformat(p["due_date"].replace("Z", ""))
            days_until_due = (due_date - now).days
            p["days_until_due"] = days_until_due
            p["is_overdue"] = days_until_due < 0 and p["status"] != "paid"
        except (ValueError, KeyError):
            p["days_until_due"] = None
            p["is_overdue"] = False
    
    return {"payments": payments}


@router.get("/pending")
async def get_pending_payments(current_user: dict = Depends(get_current_user)):
    """Get pending payments for current user"""
    filters = {"status": "pending"}
    
    if current_user["role"] == "supplier":
        filters["supplier_id"] = current_user["id"]
    elif current_user["role"] == "client":
        filters["client_id"] = current_user["id"]
    
    return db.payments.find_all(filters)


@router.get("/{payment_id}")
async def get_payment(
    payment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific payment"""
    payment = db.payments.find_by_id(payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_payment(
    request: PaymentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new payment"""
    data = request.model_dump()
    data["created_by"] = current_user["id"]
    data["status"] = "pending"
    
    if current_user["role"] == "admin":
        pass
    elif current_user["role"] == "supplier":
        data["supplier_id"] = current_user["id"]
    elif current_user["role"] == "client":
        data["client_id"] = current_user["id"]
    
    payment = db.payments.create(data)
    
    if current_user["role"] != "admin":
        db.notifications.create({
            "type": "payment",
            "title": "New Payment Created",
            "message": f"A {request.type} payment of ${request.amount:.2f} has been created",
            "target_role": "admin",
            "related_id": payment["id"],
            "read": False
        })
    else:
        if data.get("supplier_id"):
            db.notifications.create({
                "type": "payment",
                "title": "Payment Assigned",
                "message": f"A {request.type} payment of ${request.amount:.2f} has been assigned to you",
                "user_id": data["supplier_id"],
                "related_id": payment["id"],
                "read": False
            })
        if data.get("client_id"):
            db.notifications.create({
                "type": "payment",
                "title": "Payment Assigned",
                "message": f"A {request.type} payment of ${request.amount:.2f} has been assigned to you",
                "user_id": data["client_id"],
                "related_id": payment["id"],
                "read": False
            })
    
    return payment


@router.put("/{payment_id}")
async def update_payment(
    payment_id: str,
    request: PaymentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a payment"""
    payment = db.payments.find_by_id(payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    if current_user["role"] != "admin" and payment.get("created_by") != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    return db.payments.update(payment_id, update_data)


@router.put("/{payment_id}/pay")
async def mark_as_paid(
    payment_id: str,
    request: PaymentMarkPaid,
    current_user: dict = Depends(get_current_user)
):
    """Mark payment as paid with cross-role notifications"""
    payment = db.payments.find_by_id(payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    if payment["status"] == "paid":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment already marked as paid")
    
    updated = db.payments.mark_as_paid(payment_id, request.paid_date)
    user_name = f"{current_user['first_name']} {current_user['last_name']}"
    
    if current_user["role"] != "admin":
        db.notifications.create({
            "type": "payment_confirmed",
            "title": "Payment Confirmed",
            "message": f"{user_name} has marked a ${payment['amount']:.2f} payment as paid",
            "target_role": "admin",
            "related_id": payment_id,
            "read": False
        })
    
    if payment.get("supplier_id") and payment["supplier_id"] != current_user["id"]:
        db.notifications.create({
            "type": "payment_confirmed",
            "title": "Payment Confirmed",
            "message": f"A ${payment['amount']:.2f} payment has been marked as paid",
            "user_id": payment["supplier_id"],
            "related_id": payment_id,
            "read": False
        })
    
    if payment.get("client_id") and payment["client_id"] != current_user["id"]:
        db.notifications.create({
            "type": "payment_confirmed",
            "title": "Payment Confirmed",
            "message": f"A ${payment['amount']:.2f} payment has been marked as paid",
            "user_id": payment["client_id"],
            "related_id": payment_id,
            "read": False
        })
    
    return updated


@router.delete("/{payment_id}")
async def delete_payment(
    payment_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a payment (admin only)"""
    if not db.payments.delete(payment_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return {"success": True}
