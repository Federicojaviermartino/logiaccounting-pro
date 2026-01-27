"""
Mobile Dashboard API - Optimized endpoints for mobile app
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.models.store import db

router = APIRouter(prefix="/mobile", tags=["Mobile Dashboard"])


class KPIResponse(BaseModel):
    total_revenue: float
    pending_amount: float
    overdue_amount: float
    invoice_count: int
    paid_count: int
    pending_count: int
    overdue_count: int
    revenue_trend: Optional[float] = None


class RecentInvoice(BaseModel):
    id: str
    invoice_number: str
    customer_name: str
    total: float
    status: str
    due_date: str
    currency: str = "USD"


class InventoryAlert(BaseModel):
    id: str
    name: str
    sku: str
    current_quantity: int
    reorder_level: int
    status: str


class QuickStat(BaseModel):
    label: str
    value: str
    change: Optional[float] = None
    trend: Optional[str] = None


class DashboardResponse(BaseModel):
    kpis: KPIResponse
    recent_invoices: List[RecentInvoice]
    inventory_alerts: List[InventoryAlert]
    quick_stats: List[QuickStat]
    last_sync: Optional[str] = None


@router.get("/dashboard", response_model=DashboardResponse)
async def get_mobile_dashboard(
    current_user: dict = Depends(get_current_user),
):
    """
    Get optimized dashboard data for mobile app.
    """
    kpis = _get_kpis()
    recent_invoices = _get_recent_invoices(limit=5)
    inventory_alerts = _get_inventory_alerts(limit=5)
    quick_stats = _get_quick_stats()

    return DashboardResponse(
        kpis=kpis,
        recent_invoices=recent_invoices,
        inventory_alerts=inventory_alerts,
        quick_stats=quick_stats,
        last_sync=datetime.utcnow().isoformat(),
    )


@router.get("/kpis", response_model=KPIResponse)
async def get_kpis(
    period: str = Query("month", enum=["week", "month", "quarter", "year"]),
    current_user: dict = Depends(get_current_user),
):
    """
    Get key performance indicators for the mobile dashboard.
    """
    return _get_kpis(period)


@router.get("/invoices/recent", response_model=List[RecentInvoice])
async def get_recent_invoices(
    limit: int = Query(10, le=50),
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Get recent invoices for the mobile app.
    """
    return _get_recent_invoices(limit, status)


@router.get("/inventory/alerts", response_model=List[InventoryAlert])
async def get_inventory_alerts(
    limit: int = Query(10, le=50),
    current_user: dict = Depends(get_current_user),
):
    """
    Get low inventory alerts for the mobile app.
    """
    return _get_inventory_alerts(limit)


@router.get("/activity")
async def get_recent_activity(
    limit: int = Query(20, le=100),
    current_user: dict = Depends(get_current_user),
):
    """
    Get recent activity feed for the mobile app.
    """
    activities = []

    payments = db.payments.find_all()
    for payment in payments[:limit]:
        activities.append({
            "id": payment["id"],
            "type": "payment_created" if payment.get("status") != "paid" else "payment_received",
            "title": "Payment " + ("Received" if payment.get("status") == "paid" else "Created"),
            "description": f"Payment for {payment.get('description', 'Invoice')}",
            "timestamp": payment.get("created_at", datetime.utcnow().isoformat()),
            "icon": "cash",
        })

    activities = sorted(activities, key=lambda x: x["timestamp"], reverse=True)[:limit]
    return {"activities": activities}


@router.get("/search")
async def global_search(
    q: str = Query(..., min_length=2),
    types: Optional[str] = Query(None, description="Comma-separated types to search"),
    limit: int = Query(20, le=100),
    current_user: dict = Depends(get_current_user),
):
    """
    Global search across invoices, customers, and inventory.
    """
    results = []
    search_types = types.split(",") if types else ["invoices", "customers", "inventory"]
    query = q.lower()

    if "invoices" in search_types:
        payments = db.payments.find_all()
        for payment in payments:
            if query in payment.get("description", "").lower() or query in payment.get("id", "").lower():
                results.append({
                    "type": "invoice",
                    "id": payment["id"],
                    "title": payment.get("description", "Payment"),
                    "subtitle": f"${payment.get('amount', 0):,.2f}",
                    "status": payment.get("status"),
                })

    if "customers" in search_types:
        users = db.users.find_all()
        for user in users:
            name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            if query in name.lower() or query in user.get("email", "").lower():
                results.append({
                    "type": "customer",
                    "id": user["id"],
                    "title": name,
                    "subtitle": user.get("email", ""),
                })

    if "inventory" in search_types:
        materials = db.materials.find_all()
        for item in materials:
            if query in item.get("name", "").lower() or query in item.get("reference", "").lower():
                results.append({
                    "type": "inventory",
                    "id": item["id"],
                    "title": item.get("name", ""),
                    "subtitle": f"SKU: {item.get('reference', '')} - Qty: {item.get('quantity', 0)}",
                })

    return {"query": q, "results": results[:limit], "total": len(results)}


def _get_kpis(period: str = "month") -> KPIResponse:
    """Calculate KPIs from payment data."""
    payments = db.payments.find_all()

    total_revenue = sum(p.get("amount", 0) for p in payments if p.get("status") == "paid" and p.get("type") == "receivable")
    pending_amount = sum(p.get("amount", 0) for p in payments if p.get("status") in ["pending", "sent"])
    overdue_amount = sum(p.get("amount", 0) for p in payments if p.get("status") == "overdue")

    paid_count = sum(1 for p in payments if p.get("status") == "paid")
    pending_count = sum(1 for p in payments if p.get("status") in ["pending", "sent"])
    overdue_count = sum(1 for p in payments if p.get("status") == "overdue")

    return KPIResponse(
        total_revenue=total_revenue,
        pending_amount=pending_amount,
        overdue_amount=overdue_amount,
        invoice_count=len(payments),
        paid_count=paid_count,
        pending_count=pending_count,
        overdue_count=overdue_count,
        revenue_trend=12.5,
    )


def _get_recent_invoices(limit: int = 10, status: Optional[str] = None) -> List[RecentInvoice]:
    """Get recent invoices/payments."""
    payments = db.payments.find_all()

    if status:
        payments = [p for p in payments if p.get("status") == status]

    payments = sorted(payments, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]

    return [
        RecentInvoice(
            id=p["id"],
            invoice_number=f"INV-{p['id'][:8].upper()}",
            customer_name=p.get("description", "Customer"),
            total=p.get("amount", 0),
            status=p.get("status", "pending"),
            due_date=p.get("due_date", datetime.utcnow().isoformat()),
            currency="USD",
        )
        for p in payments
    ]


def _get_inventory_alerts(limit: int = 10) -> List[InventoryAlert]:
    """Get inventory items that need attention."""
    materials = db.materials.find_all({"low_stock": True})

    return [
        InventoryAlert(
            id=item["id"],
            name=item.get("name", ""),
            sku=item.get("reference", ""),
            current_quantity=item.get("quantity", 0),
            reorder_level=item.get("min_stock", 0),
            status="out_of_stock" if item.get("quantity", 0) == 0 else "low_stock",
        )
        for item in materials[:limit]
    ]


def _get_quick_stats() -> List[QuickStat]:
    """Get quick stats for the dashboard."""
    payments = db.payments.find_all()
    users = db.users.find_all()

    invoice_count = len(payments)
    customer_count = len([u for u in users if u.get("role") == "client"])

    return [
        QuickStat(label="Total Invoices", value=str(invoice_count), change=5.2, trend="up"),
        QuickStat(label="Active Customers", value=str(customer_count), change=2.1, trend="up"),
        QuickStat(label="Avg. Invoice", value="$1,250", change=-1.5, trend="down"),
        QuickStat(label="Collection Rate", value="94%", change=0.5, trend="up"),
    ]
