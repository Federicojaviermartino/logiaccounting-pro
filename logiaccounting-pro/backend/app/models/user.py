"""
User model for type hints in route dependencies.
"""

from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class User(BaseModel):
    """User model representing an authenticated user."""
    id: str
    email: str
    name: str
    role: str
    company_id: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
