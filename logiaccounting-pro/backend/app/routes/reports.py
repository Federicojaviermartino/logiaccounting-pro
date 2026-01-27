"""
Reports and analytics routes
"""

from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from app.models.store import db
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    
    projects = db.projects._data
    active_projects = len([p for p in projects if p.get("status") == "active"])
    
    payments = db.payments._data
    pending_payments = [p for p in payments if p.get("status") in ["pending", "overdue"]]
    
    transactions = db.transactions._data
    monthly_trans = []
    for t in transactions:
        try:
            t_date = datetime.fromisoformat(t.get("date", t["created_at"]).replace("Z", ""))
            if t_date >= month_start:
                monthly_trans.append(t)
        except (ValueError, KeyError):
            pass
    
    monthly_revenue = sum(t["amount"] for t in monthly_trans if t["type"] == "income")
    monthly_expenses = sum(t["amount"] for t in monthly_trans if t["type"] == "expense")
    
    materials = db.materials._data
    low_stock = len([m for m in materials if m["quantity"] <= m.get("min_stock", 0)])
    
    overdue = len([p for p in payments if p.get("status") != "paid"])
    
    data = {
        "active_projects": active_projects,
        "pending_payments_count": len(pending_payments),
        "pending_payments_amount": sum(p["amount"] for p in pending_payments),
        "monthly_revenue": monthly_revenue,
        "monthly_expenses": monthly_expenses,
        "profit_margin": round((monthly_revenue - monthly_expenses) / monthly_revenue * 100, 1) if monthly_revenue > 0 else 0,
        "low_stock_alerts": low_stock,
        "overdue_payments": overdue
    }
    
    if current_user["role"] in ["client", "supplier"]:
        key = "client_id" if current_user["role"] == "client" else "supplier_id"
        my_payments = [p for p in pending_payments if p.get(key) == current_user["id"]]
        data["my_pending_payments"] = len(my_payments)
        data["my_pending_amount"] = sum(p["amount"] for p in my_payments)
    
    return data


@router.get("/cash-flow")
async def get_cash_flow(
    months: int = Query(6, ge=1, le=12),
    current_user: dict = Depends(require_roles("admin"))
):
    """Get cash flow data for charts"""
    now = datetime.utcnow()
    result = []
    
    for i in range(months - 1, -1, -1):
        target_date = now - timedelta(days=i * 30)
        month_start = datetime(target_date.year, target_date.month, 1)
        
        if target_date.month == 12:
            month_end = datetime(target_date.year + 1, 1, 1)
        else:
            month_end = datetime(target_date.year, target_date.month + 1, 1)
        
        month_name = month_start.strftime("%b %Y")
        
        transactions = db.transactions._data
        month_trans = []
        for t in transactions:
            try:
                t_date = datetime.fromisoformat(t.get("date", t["created_at"]).replace("Z", ""))
                if month_start <= t_date < month_end:
                    month_trans.append(t)
            except (ValueError, KeyError):
                pass
        
        result.append({
            "month": month_name,
            "income": sum(t["amount"] for t in month_trans if t["type"] == "income"),
            "expenses": sum(t["amount"] for t in month_trans if t["type"] == "expense")
        })
    
    return result


@router.get("/expenses-by-category")
async def get_expenses_by_category(
    current_user: dict = Depends(require_roles("admin"))
):
    """Get expenses grouped by category"""
    categories = [c for c in db.categories._data if c.get("type") == "expense"]
    transactions = [t for t in db.transactions._data if t["type"] == "expense"]
    
    result = []
    for cat in categories:
        amount = sum(t["amount"] for t in transactions if t.get("category_id") == cat["id"])
        if amount > 0:
            result.append({"id": cat["id"], "name": cat["name"], "amount": amount})
    
    return result


@router.get("/project-profitability")
async def get_project_profitability(
    current_user: dict = Depends(require_roles("admin"))
):
    """Get project profitability analysis"""
    projects = db.projects._data
    transactions = db.transactions._data
    
    result = []
    for p in projects:
        proj_trans = [t for t in transactions if t.get("project_id") == p["id"]]
        income = sum(t["amount"] for t in proj_trans if t["type"] == "income")
        expenses = sum(t["amount"] for t in proj_trans if t["type"] == "expense")
        profit = income - expenses
        
        result.append({
            "id": p["id"],
            "code": p.get("code", "N/A"),
            "name": p["name"],
            "status": p.get("status", "unknown"),
            "budget": p.get("budget", 0),
            "income": income,
            "expenses": expenses,
            "profit": profit,
            "margin": round(profit / income * 100, 1) if income > 0 else 0
        })
    
    return result


@router.get("/inventory-summary")
async def get_inventory_summary(current_user: dict = Depends(get_current_user)):
    """Get inventory summary"""
    materials = db.materials._data
    
    return {
        "total_items": len(materials),
        "total_value": sum(m["quantity"] * m.get("unit_cost", 0) for m in materials),
        "low_stock_count": len([m for m in materials if m["quantity"] <= m.get("min_stock", 0)]),
        "by_state": {
            "available": len([m for m in materials if m.get("state") == "available"]),
            "reserved": len([m for m in materials if m.get("state") == "reserved"]),
            "damaged": len([m for m in materials if m.get("state") == "damaged"])
        }
    }


@router.get("/payment-summary")
async def get_payment_summary(current_user: dict = Depends(get_current_user)):
    """Get payment summary"""
    payments = db.payments._data
    now = datetime.utcnow()
    
    pending = [p for p in payments if p.get("status") == "pending"]
    paid = [p for p in payments if p.get("status") == "paid"]
    
    overdue = []
    for p in payments:
        if p.get("status") != "paid":
            try:
                due_date = datetime.fromisoformat(p["due_date"].replace("Z", ""))
                if due_date < now:
                    overdue.append(p)
            except (ValueError, KeyError):
                pass
    
    return {
        "by_status": {
            "pending": len(pending),
            "overdue": len(overdue),
            "paid": len(paid)
        },
        "amounts": {
            "pending": sum(p["amount"] for p in pending),
            "overdue": sum(p["amount"] for p in overdue),
            "paid": sum(p["amount"] for p in paid)
        },
        "total_payable": sum(p["amount"] for p in payments if p.get("type") == "payable" and p.get("status") != "paid"),
        "total_receivable": sum(p["amount"] for p in payments if p.get("type") == "receivable" and p.get("status") != "paid")
    }
