"""
Supplier Portal routes
Limited access for suppliers to view their data
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.store import db
from app.utils.auth import get_current_user

router = APIRouter()


def get_supplier_user(current_user: dict = Depends(get_current_user)):
    """Ensure user is a supplier"""
    if current_user.get("role") not in ["supplier", "admin"]:
        raise HTTPException(status_code=403, detail="Supplier access required")
    return current_user


@router.get("/dashboard")
async def supplier_dashboard(current_user: dict = Depends(get_supplier_user)):
    """Get supplier dashboard data"""
    supplier_email = current_user["email"]

    # Get transactions where vendor matches (purchases from this supplier)
    if current_user["role"] == "admin":
        transactions = db.transactions.find_all()
        payments = db.payments.find_all()
    else:
        transactions = [
            t for t in db.transactions.find_all()
            if t.get("vendor_email") == supplier_email or t.get("vendor_name") == supplier_email
        ]
        payments = [
            p for p in db.payments.find_all()
            if p.get("vendor_email") == supplier_email
        ]

    # Stats
    total_orders = len(transactions)
    total_revenue = sum(t.get("amount", 0) for t in transactions)
    total_paid = sum(p.get("amount", 0) for p in payments if p.get("status") == "paid")
    total_pending = sum(p.get("amount", 0) for p in payments if p.get("status") == "pending")

    return {
        "stats": {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_paid": total_paid,
            "total_pending": total_pending
        },
        "recent_orders": transactions[:10],
        "pending_payments": [p for p in payments if p.get("status") == "pending"][:5]
    }


@router.get("/orders")
async def supplier_orders(current_user: dict = Depends(get_supplier_user)):
    """Get supplier's orders/transactions"""
    supplier_email = current_user["email"]

    if current_user["role"] == "admin":
        transactions = [t for t in db.transactions.find_all() if t.get("type") == "expense"]
    else:
        transactions = [
            t for t in db.transactions.find_all()
            if (t.get("vendor_email") == supplier_email or t.get("vendor_name") == supplier_email)
            and t.get("type") == "expense"
        ]

    return {"orders": transactions}


@router.get("/payments")
async def supplier_payments(current_user: dict = Depends(get_supplier_user)):
    """Get supplier's payments"""
    supplier_email = current_user["email"]

    if current_user["role"] == "admin":
        payments = [p for p in db.payments.find_all() if p.get("type") == "payable"]
    else:
        payments = [
            p for p in db.payments.find_all()
            if p.get("vendor_email") == supplier_email and p.get("type") == "payable"
        ]

    return {"payments": payments}


@router.get("/catalog")
async def supplier_catalog(current_user: dict = Depends(get_supplier_user)):
    """Get supplier's product catalog"""
    supplier_email = current_user["email"]

    # For demo, return materials that could be from this supplier
    if current_user["role"] == "admin":
        materials = db.materials.find_all()
    else:
        materials = [
            m for m in db.materials.find_all()
            if m.get("supplier_email") == supplier_email
        ]

    return {"products": materials}


@router.get("/profile")
async def supplier_profile(current_user: dict = Depends(get_supplier_user)):
    """Get supplier profile"""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user.get("name", ""),
        "company": current_user.get("company", ""),
        "phone": current_user.get("phone", ""),
        "address": current_user.get("address", "")
    }
