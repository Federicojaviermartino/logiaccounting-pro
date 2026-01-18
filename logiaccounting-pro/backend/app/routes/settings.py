"""
User and system settings routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.models.store import db
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


class UserPreferences(BaseModel):
    """User preference settings"""
    language: str = "en"
    theme: str = "light"
    date_format: str = "MM/DD/YYYY"
    time_format: str = "12h"
    currency: str = "USD"
    notifications_email: bool = True
    notifications_push: bool = True
    dashboard_default_view: str = "overview"


class SystemSettings(BaseModel):
    """System-wide settings (admin only)"""
    company_name: str = "LogiAccounting Pro"
    default_tax_rate: float = 0.21
    payment_terms_days: int = 30
    low_stock_threshold: int = 10
    enable_ai_features: bool = True
    enable_email_notifications: bool = True


# In-memory settings storage
user_preferences = {}
system_settings = SystemSettings()


@router.get("/user")
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    """Get current user's preferences"""
    user_id = current_user["id"]
    prefs = user_preferences.get(user_id, UserPreferences())
    return {"preferences": prefs.model_dump()}


@router.put("/user")
async def update_user_preferences(
    prefs: UserPreferences,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's preferences"""
    user_id = current_user["id"]
    user_preferences[user_id] = prefs
    return {"preferences": prefs.model_dump(), "message": "Preferences updated"}


@router.get("/system")
async def get_system_settings(current_user: dict = Depends(get_current_user)):
    """Get system settings (visible to all, editable by admin)"""
    return {"settings": system_settings.model_dump()}


@router.put("/system")
async def update_system_settings(
    settings: SystemSettings,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update system settings (admin only)"""
    global system_settings
    system_settings = settings
    return {"settings": settings.model_dump(), "message": "System settings updated"}


@router.get("/available-options")
async def get_available_options():
    """Get available options for settings dropdowns"""
    return {
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Español"}
        ],
        "themes": [
            {"code": "light", "name": "Light"},
            {"code": "dark", "name": "Dark"},
            {"code": "system", "name": "System"}
        ],
        "date_formats": [
            {"code": "MM/DD/YYYY", "example": "01/15/2024"},
            {"code": "DD/MM/YYYY", "example": "15/01/2024"},
            {"code": "YYYY-MM-DD", "example": "2024-01-15"}
        ],
        "time_formats": [
            {"code": "12h", "example": "2:30 PM"},
            {"code": "24h", "example": "14:30"}
        ],
        "currencies": [
            {"code": "USD", "symbol": "$", "name": "US Dollar"},
            {"code": "EUR", "symbol": "€", "name": "Euro"},
            {"code": "GBP", "symbol": "£", "name": "British Pound"},
            {"code": "ARS", "symbol": "$", "name": "Argentine Peso"}
        ]
    }
