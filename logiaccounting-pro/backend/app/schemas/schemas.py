"""
Pydantic schemas for request/response validation
"""

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# Auth schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    success: bool = True
    token: str
    user: dict


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    role: str = Field(..., pattern="^(client|supplier)$")
    company_name: Optional[str] = None
    phone: Optional[str] = None


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|inactive|suspended)$")


# Inventory schemas
class MaterialCreate(BaseModel):
    reference: str
    name: str
    description: Optional[str] = None
    category_id: Optional[str] = None
    location_id: Optional[str] = None
    quantity: float = 0
    min_stock: float = 0
    unit: str = "units"
    unit_cost: float = 0
    state: str = "available"


class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    location_id: Optional[str] = None
    quantity: Optional[float] = None
    min_stock: Optional[float] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = None
    state: Optional[str] = None


class CategoryCreate(BaseModel):
    name: str
    type: str = Field(..., pattern="^(material|income|expense)$")


class LocationCreate(BaseModel):
    name: str
    code: str
    address: Optional[str] = None


# Project schemas
class ProjectCreate(BaseModel):
    name: str
    client: Optional[str] = None
    client_id: Optional[str] = None
    description: Optional[str] = None
    budget: float = 0
    status: str = "planning"
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client: Optional[str] = None
    client_id: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[float] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


# Movement schemas
class MovementCreate(BaseModel):
    type: str = Field(..., pattern="^(entry|exit)$")
    material_id: str
    quantity: float = Field(..., gt=0)
    project_id: Optional[str] = None
    notes: Optional[str] = None


# Transaction schemas
class TransactionCreate(BaseModel):
    type: str = Field(..., pattern="^(income|expense)$")
    category_id: Optional[str] = None
    project_id: Optional[str] = None
    amount: float = Field(..., gt=0)
    tax_amount: float = 0
    description: Optional[str] = None
    date: Optional[str] = None
    invoice_number: Optional[str] = None


class TransactionUpdate(BaseModel):
    category_id: Optional[str] = None
    project_id: Optional[str] = None
    amount: Optional[float] = None
    tax_amount: Optional[float] = None
    description: Optional[str] = None
    date: Optional[str] = None
    invoice_number: Optional[str] = None


# Payment schemas
class PaymentCreate(BaseModel):
    type: str = Field(..., pattern="^(payable|receivable)$")
    amount: float = Field(..., gt=0)
    due_date: str
    description: Optional[str] = None
    reference: Optional[str] = None
    project_id: Optional[str] = None
    supplier_id: Optional[str] = None
    client_id: Optional[str] = None


class PaymentUpdate(BaseModel):
    amount: Optional[float] = None
    due_date: Optional[str] = None
    description: Optional[str] = None
    reference: Optional[str] = None
    project_id: Optional[str] = None


class PaymentMarkPaid(BaseModel):
    paid_date: Optional[str] = None
