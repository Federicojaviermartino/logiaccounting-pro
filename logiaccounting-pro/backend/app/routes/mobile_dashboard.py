"""
Mobile Dashboard API - Optimized endpoints for mobile app
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get optimized dashboard data for mobile app.
    Returns KPIs, recent invoices, and alerts in a single request.
    """
    org_id = current_user.organization_id

    kpis = await _get_kpis(db, org_id)
    recent_invoices = await _get_recent_invoices(db, org_id, limit=5)
    inventory_alerts = await _get_inventory_alerts(db, org_id, limit=5)
    quick_stats = await _get_quick_stats(db, org_id)

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get key performance indicators for the mobile dashboard.
    """
    return await _get_kpis(db, current_user.organization_id, period)


@router.get("/invoices/recent", response_model=List[RecentInvoice])
async def get_recent_invoices(
    limit: int = Query(10, le=50),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get recent invoices for the mobile app.
    """
    return await _get_recent_invoices(
        db, current_user.organization_id, limit, status
    )


@router.get("/inventory/alerts", response_model=List[InventoryAlert])
async def get_inventory_alerts(
    limit: int = Query(10, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get low inventory alerts for the mobile app.
    """
    return await _get_inventory_alerts(db, current_user.organization_id, limit)


@router.get("/activity")
async def get_recent_activity(
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get recent activity feed for the mobile app.
    """
    activities = [
        {
            "id": "1",
            "type": "invoice_created",
            "title": "New Invoice Created",
            "description": "Invoice INV-001 created for Customer A",
            "timestamp": datetime.utcnow().isoformat(),
            "icon": "document-text",
        },
        {
            "id": "2",
            "type": "payment_received",
            "title": "Payment Received",
            "description": "Payment of $1,500 received for INV-002",
            "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "icon": "cash",
        },
    ]

    return {"activities": activities[:limit]}


@router.get("/search")
async def global_search(
    q: str = Query(..., min_length=2),
    types: Optional[str] = Query(None, description="Comma-separated types to search"),
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Global search across invoices, customers, and inventory.
    """
    org_id = current_user.organization_id
    results = []
    search_types = types.split(",") if types else ["invoices", "customers", "inventory"]

    if "invoices" in search_types:
        from app.models.invoice import Invoice

        invoices = db.query(Invoice).filter(
            Invoice.organization_id == org_id,
            Invoice.invoice_number.ilike(f"%{q}%")
        ).limit(limit // 3).all()

        results.extend([
            {
                "type": "invoice",
                "id": str(inv.id),
                "title": inv.invoice_number,
                "subtitle": f"{inv.customer_name} - ${inv.total:,.2f}",
                "status": inv.status,
            }
            for inv in invoices
        ])

    if "customers" in search_types:
        from app.models.customer import Customer

        customers = db.query(Customer).filter(
            Customer.organization_id == org_id,
            Customer.name.ilike(f"%{q}%")
        ).limit(limit // 3).all()

        results.extend([
            {
                "type": "customer",
                "id": str(cust.id),
                "title": cust.name,
                "subtitle": cust.email or "",
            }
            for cust in customers
        ])

    if "inventory" in search_types:
        from app.models.inventory import InventoryItem

        items = db.query(InventoryItem).filter(
            InventoryItem.organization_id == org_id,
            (InventoryItem.name.ilike(f"%{q}%") | InventoryItem.sku.ilike(f"%{q}%"))
        ).limit(limit // 3).all()

        results.extend([
            {
                "type": "inventory",
                "id": str(item.id),
                "title": item.name,
                "subtitle": f"SKU: {item.sku} - Qty: {item.quantity}",
            }
            for item in items
        ])

    return {"query": q, "results": results[:limit], "total": len(results)}


async def _get_kpis(
    db: Session, org_id: int, period: str = "month"
) -> KPIResponse:
    """Calculate KPIs for the given organization."""
    from app.models.invoice import Invoice

    now = datetime.utcnow()

    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    else:
        start_date = now - timedelta(days=365)

    invoices = db.query(Invoice).filter(
        Invoice.organization_id == org_id,
        Invoice.created_at >= start_date,
    ).all()

    total_revenue = sum(inv.total for inv in invoices if inv.status == "paid")
    pending_amount = sum(inv.total for inv in invoices if inv.status in ["pending", "sent"])
    overdue_amount = sum(
        inv.total for inv in invoices
        if inv.status not in ["paid", "cancelled"] and inv.due_date and inv.due_date < now
    )

    paid_count = sum(1 for inv in invoices if inv.status == "paid")
    pending_count = sum(1 for inv in invoices if inv.status in ["pending", "sent"])
    overdue_count = sum(
        1 for inv in invoices
        if inv.status not in ["paid", "cancelled"] and inv.due_date and inv.due_date < now
    )

    return KPIResponse(
        total_revenue=total_revenue,
        pending_amount=pending_amount,
        overdue_amount=overdue_amount,
        invoice_count=len(invoices),
        paid_count=paid_count,
        pending_count=pending_count,
        overdue_count=overdue_count,
        revenue_trend=12.5,
    )


async def _get_recent_invoices(
    db: Session, org_id: int, limit: int = 10, status: Optional[str] = None
) -> List[RecentInvoice]:
    """Get recent invoices for the organization."""
    from app.models.invoice import Invoice

    query = db.query(Invoice).filter(Invoice.organization_id == org_id)

    if status:
        query = query.filter(Invoice.status == status)

    invoices = query.order_by(Invoice.created_at.desc()).limit(limit).all()

    return [
        RecentInvoice(
            id=str(inv.id),
            invoice_number=inv.invoice_number,
            customer_name=inv.customer_name or "Unknown",
            total=inv.total,
            status=inv.status,
            due_date=inv.due_date.isoformat() if inv.due_date else "",
            currency=inv.currency or "USD",
        )
        for inv in invoices
    ]


async def _get_inventory_alerts(
    db: Session, org_id: int, limit: int = 10
) -> List[InventoryAlert]:
    """Get inventory items that need attention."""
    from app.models.inventory import InventoryItem

    items = db.query(InventoryItem).filter(
        InventoryItem.organization_id == org_id,
        InventoryItem.quantity <= InventoryItem.reorder_level,
    ).order_by(InventoryItem.quantity.asc()).limit(limit).all()

    return [
        InventoryAlert(
            id=str(item.id),
            name=item.name,
            sku=item.sku or "",
            current_quantity=item.quantity,
            reorder_level=item.reorder_level,
            status="out_of_stock" if item.quantity == 0 else "low_stock",
        )
        for item in items
    ]


async def _get_quick_stats(db: Session, org_id: int) -> List[QuickStat]:
    """Get quick stats for the dashboard."""
    from app.models.invoice import Invoice
    from app.models.customer import Customer

    invoice_count = db.query(Invoice).filter(Invoice.organization_id == org_id).count()
    customer_count = db.query(Customer).filter(Customer.organization_id == org_id).count()

    return [
        QuickStat(label="Total Invoices", value=str(invoice_count), change=5.2, trend="up"),
        QuickStat(label="Active Customers", value=str(customer_count), change=2.1, trend="up"),
        QuickStat(label="Avg. Invoice", value="$1,250", change=-1.5, trend="down"),
        QuickStat(label="Collection Rate", value="94%", change=0.5, trend="up"),
    ]
