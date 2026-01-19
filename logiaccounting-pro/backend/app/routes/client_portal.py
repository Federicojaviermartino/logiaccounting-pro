"""
Client Portal routes
Limited access for clients to view their data
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.store import db
from app.utils.auth import get_current_user

router = APIRouter()


def get_client_user(current_user: dict = Depends(get_current_user)):
    """Ensure user is a client"""
    if current_user.get("role") not in ["client", "admin"]:
        raise HTTPException(status_code=403, detail="Client access required")
    return current_user


@router.get("/dashboard")
async def client_dashboard(current_user: dict = Depends(get_client_user)):
    """Get client dashboard data"""
    client_email = current_user["email"]

    # Get projects where client matches
    projects = [p for p in db.projects.find_all() if p.get("client") == client_email or current_user["role"] == "admin"]

    # Get related transactions and payments
    project_ids = [p["id"] for p in projects]

    transactions = [t for t in db.transactions.find_all() if t.get("project_id") in project_ids]
    payments = [p for p in db.payments.find_all() if p.get("project_id") in project_ids]

    # Stats
    total_invoiced = sum(t.get("amount", 0) for t in transactions if t.get("type") == "income")
    total_paid = sum(p.get("amount", 0) for p in payments if p.get("status") == "paid")
    total_pending = sum(p.get("amount", 0) for p in payments if p.get("status") == "pending")

    return {
        "stats": {
            "total_projects": len(projects),
            "active_projects": len([p for p in projects if p.get("status") == "active"]),
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "total_pending": total_pending
        },
        "recent_projects": projects[:5],
        "recent_invoices": transactions[:5],
        "pending_payments": [p for p in payments if p.get("status") == "pending"][:5]
    }


@router.get("/projects")
async def client_projects(current_user: dict = Depends(get_client_user)):
    """Get client's projects"""
    client_email = current_user["email"]

    if current_user["role"] == "admin":
        projects = db.projects.find_all()
    else:
        projects = [p for p in db.projects.find_all() if p.get("client") == client_email]

    # Remove sensitive fields
    safe_projects = []
    for p in projects:
        safe_projects.append({
            "id": p.get("id"),
            "name": p.get("name"),
            "description": p.get("description"),
            "status": p.get("status"),
            "progress": p.get("progress", 0),
            "start_date": p.get("start_date"),
            "end_date": p.get("end_date")
            # Note: budget/spent not exposed to clients
        })

    return {"projects": safe_projects}


@router.get("/projects/{project_id}")
async def client_project_detail(
    project_id: str,
    current_user: dict = Depends(get_client_user)
):
    """Get project details"""
    project = db.projects.find_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Verify ownership (unless admin)
    if current_user["role"] != "admin" and project.get("client") != current_user["email"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": project.get("id"),
        "name": project.get("name"),
        "description": project.get("description"),
        "status": project.get("status"),
        "progress": project.get("progress", 0),
        "start_date": project.get("start_date"),
        "end_date": project.get("end_date")
    }


@router.get("/invoices")
async def client_invoices(current_user: dict = Depends(get_client_user)):
    """Get client's invoices"""
    client_email = current_user["email"]

    # Get projects
    if current_user["role"] == "admin":
        projects = db.projects.find_all()
    else:
        projects = [p for p in db.projects.find_all() if p.get("client") == client_email]

    project_ids = [p["id"] for p in projects]
    project_names = {p["id"]: p["name"] for p in projects}

    # Get income transactions (invoices)
    transactions = [
        t for t in db.transactions.find_all()
        if t.get("project_id") in project_ids and t.get("type") == "income"
    ]

    # Add project name
    for t in transactions:
        t["project_name"] = project_names.get(t.get("project_id"), "N/A")

    return {"invoices": transactions}


@router.get("/payments")
async def client_payments(current_user: dict = Depends(get_client_user)):
    """Get client's payments"""
    client_email = current_user["email"]

    # Get projects
    if current_user["role"] == "admin":
        projects = db.projects.find_all()
    else:
        projects = [p for p in db.projects.find_all() if p.get("client") == client_email]

    project_ids = [p["id"] for p in projects]
    project_names = {p["id"]: p["name"] for p in projects}

    # Get payments
    payments = [p for p in db.payments.find_all() if p.get("project_id") in project_ids]

    for p in payments:
        p["project_name"] = project_names.get(p.get("project_id"), "N/A")

    return {"payments": payments}


@router.get("/profile")
async def client_profile(current_user: dict = Depends(get_client_user)):
    """Get client profile"""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user.get("name", ""),
        "company": current_user.get("company", ""),
        "phone": current_user.get("phone", "")
    }
