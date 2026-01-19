"""
LogiAccounting Pro - FastAPI Backend
Enterprise logistics and accounting platform
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.routes import (
    auth, inventory, projects, movements, transactions, payments,
    notifications, reports, ocr, cashflow, assistant, anomaly, scheduler, settings,
    activity, bulk, email, two_factor, report_builder, backup, webhooks,
    approvals, recurring, budgets, documents, api_keys,
    # Phase 6 - Ultimate Enterprise Features
    dashboards, websocket, reconciliation, client_portal, supplier_portal,
    scheduled_reports, currencies,
    # Phase 7 - Advanced Analytics & Integrations
    audit, data_import, comments, tasks, taxes, custom_fields, calendar
)
from app.models.store import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_database()
    yield


app = FastAPI(
    title="LogiAccounting Pro API",
    description="Enterprise logistics and accounting platform with AI-powered features",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(movements.router, prefix="/api/v1/movements", tags=["Movements"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transactions"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["OCR Invoice Processing"])

# AI-Powered Features
app.include_router(cashflow.router, prefix="/api/v1/cashflow", tags=["Cash Flow Predictor"])
app.include_router(assistant.router, prefix="/api/v1/assistant", tags=["Profitability Assistant"])
app.include_router(anomaly.router, prefix="/api/v1/anomaly", tags=["Anomaly Detection"])
app.include_router(scheduler.router, prefix="/api/v1/scheduler", tags=["Payment Scheduler"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(activity.router, prefix="/api/v1/activity", tags=["Activity"])
app.include_router(bulk.router, prefix="/api/v1/bulk", tags=["Bulk Operations"])
app.include_router(email.router, prefix="/api/v1/email", tags=["Email"])
app.include_router(two_factor.router, prefix="/api/v1/2fa", tags=["Two-Factor Auth"])
app.include_router(report_builder.router, prefix="/api/v1/report-builder", tags=["Report Builder"])
app.include_router(backup.router, prefix="/api/v1/backup", tags=["Backup"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])

# Phase 5 - Enterprise Features
app.include_router(approvals.router, prefix="/api/v1/approvals", tags=["Approvals"])
app.include_router(recurring.router, prefix="/api/v1/recurring", tags=["Recurring"])
app.include_router(budgets.router, prefix="/api/v1/budgets", tags=["Budgets"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(api_keys.router, prefix="/api/v1/api-keys", tags=["API Keys"])

# Phase 6 - Ultimate Enterprise Features
app.include_router(dashboards.router, prefix="/api/v1/dashboards", tags=["Dashboard Builder"])
app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(reconciliation.router, prefix="/api/v1/reconciliation", tags=["Bank Reconciliation"])
app.include_router(client_portal.router, prefix="/api/v1/portal/client", tags=["Client Portal"])
app.include_router(supplier_portal.router, prefix="/api/v1/portal/supplier", tags=["Supplier Portal"])
app.include_router(scheduled_reports.router, prefix="/api/v1/scheduled-reports", tags=["Scheduled Reports"])
app.include_router(currencies.router, prefix="/api/v1/currencies", tags=["Currencies"])

# Phase 7 - Advanced Analytics & Integrations
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit Trail"])
app.include_router(data_import.router, prefix="/api/v1/import", tags=["Data Import"])
app.include_router(comments.router, prefix="/api/v1/comments", tags=["Comments"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(taxes.router, prefix="/api/v1/taxes", tags=["Tax Management"])
app.include_router(custom_fields.router, prefix="/api/v1/custom-fields", tags=["Custom Fields"])
app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["Calendar"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "LogiAccounting Pro API"}


@app.get("/api/v1/info")
async def api_info():
    """API information"""
    return {
        "name": "LogiAccounting Pro",
        "version": "2.0.0",
        "description": "Enterprise logistics and accounting platform with AI-powered features",
        "ai_features": {
            "ocr_invoice_processing": "Smart Invoice OCR + Auto-Categorization (Tesseract + OpenAI Vision)",
            "cash_flow_predictor": "Intelligent 30-60-90 day cash flow prediction (Prophet ML)",
            "profitability_assistant": "NLP chatbot for financial queries (Claude API)",
            "anomaly_detection": "Fraud prevention & duplicate detection (Statistical ML + Isolation Forest)",
            "payment_scheduler": "Optimized payment scheduling (Constraint optimization)"
        },
        "demo_credentials": {
            "admin": "admin@logiaccounting.demo / Demo2024!Admin",
            "client": "client@logiaccounting.demo / Demo2024!Client",
            "supplier": "supplier@logiaccounting.demo / Demo2024!Supplier"
        }
    }


# Serve React frontend in production
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve React SPA for all non-API routes"""
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
