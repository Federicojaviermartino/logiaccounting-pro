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

from app.routes import auth, inventory, projects, movements, transactions, payments, notifications, reports
from app.models.store import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_database()
    yield


app = FastAPI(
    title="LogiAccounting Pro API",
    description="Enterprise logistics and accounting platform",
    version="1.0.0",
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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "LogiAccounting Pro API"}


@app.get("/api/v1/info")
async def api_info():
    """API information"""
    return {
        "name": "LogiAccounting Pro",
        "version": "1.0.0",
        "description": "Enterprise logistics and accounting platform",
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
