"""
Product Schemas
Pydantic schemas for products and categories
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator


class ProductTypeEnum(str, Enum):
    STOCKABLE = "stockable"
    CONSUMABLE = "consumable"
    SERVICE = "service"


class ValuationMethodEnum(str, Enum):
    FIFO = "fifo"
    LIFO = "lifo"
    AVERAGE = "average"
    STANDARD = "standard"


class UOMCategoryEnum(str, Enum):
    UNIT = "unit"
    WEIGHT = "weight"
    VOLUME = "volume"
    LENGTH = "length"
    TIME = "time"


# ============== Unit of Measure ==============

class UOMCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=50)
    category: Optional[UOMCategoryEnum] = None
    base_uom_id: Optional[UUID] = None
    conversion_factor: Decimal = Field(default=Decimal("1"), gt=0)


class UOMUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[UOMCategoryEnum] = None
    base_uom_id: Optional[UUID] = None
    conversion_factor: Optional[Decimal] = None
    is_active: Optional[bool] = None


class UOMResponse(BaseModel):
    id: UUID
    code: str
    name: str
    category: Optional[str]
    base_uom_id: Optional[UUID]
    conversion_factor: float
    is_active: bool

    class Config:
        from_attributes = True


# ============== Category ==============

class CategoryCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    default_uom_id: Optional[UUID] = None
    default_valuation_method: ValuationMethodEnum = ValuationMethodEnum.FIFO


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    default_uom_id: Optional[UUID] = None
    default_valuation_method: Optional[ValuationMethodEnum] = None
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    parent_id: Optional[UUID]
    level: int
    path: Optional[str]
    default_valuation_method: Optional[str]
    is_active: bool
    children: Optional[List["CategoryResponse"]] = None

    class Config:
        from_attributes = True


# ============== Product ==============

class ProductDimensions(BaseModel):
    length: Optional[Decimal] = None
    width: Optional[Decimal] = None
    height: Optional[Decimal] = None
    uom: Optional[str] = Field(None, max_length=10)


class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    barcode: Optional[str] = Field(None, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None

    category_id: Optional[UUID] = None
    product_type: ProductTypeEnum = ProductTypeEnum.STOCKABLE

    uom_id: UUID
    purchase_uom_id: Optional[UUID] = None

    standard_cost: Decimal = Field(default=Decimal("0"), ge=0)
    list_price: Decimal = Field(default=Decimal("0"), ge=0)

    track_inventory: bool = True
    track_lots: bool = False
    track_serials: bool = False
    valuation_method: ValuationMethodEnum = ValuationMethodEnum.FIFO

    reorder_point: Decimal = Field(default=Decimal("0"), ge=0)
    reorder_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    safety_stock: Decimal = Field(default=Decimal("0"), ge=0)
    lead_time_days: int = Field(default=0, ge=0)

    weight: Optional[Decimal] = None
    weight_uom: Optional[str] = None
    dimensions: Optional[ProductDimensions] = None

    inventory_account_id: Optional[UUID] = None
    cogs_account_id: Optional[UUID] = None
    revenue_account_id: Optional[UUID] = None

    image_url: Optional[str] = None

    is_purchasable: bool = True
    is_sellable: bool = True

    @validator("track_serials")
    def serials_require_lots(cls, v, values):
        if v and not values.get("track_lots", False):
            # Serial tracking implies lot tracking
            pass  # Allow independently
        return v

    @validator("product_type")
    def service_no_inventory(cls, v, values):
        if v == ProductTypeEnum.SERVICE:
            values["track_inventory"] = False
        return v


class ProductUpdate(BaseModel):
    barcode: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

    category_id: Optional[UUID] = None

    purchase_uom_id: Optional[UUID] = None

    standard_cost: Optional[Decimal] = None
    list_price: Optional[Decimal] = None

    track_lots: Optional[bool] = None
    track_serials: Optional[bool] = None

    reorder_point: Optional[Decimal] = None
    reorder_quantity: Optional[Decimal] = None
    safety_stock: Optional[Decimal] = None
    lead_time_days: Optional[int] = None

    weight: Optional[Decimal] = None
    weight_uom: Optional[str] = None
    dimensions: Optional[ProductDimensions] = None

    inventory_account_id: Optional[UUID] = None
    cogs_account_id: Optional[UUID] = None
    revenue_account_id: Optional[UUID] = None

    image_url: Optional[str] = None

    is_active: Optional[bool] = None
    is_purchasable: Optional[bool] = None
    is_sellable: Optional[bool] = None


class ProductResponse(BaseModel):
    id: UUID
    sku: str
    barcode: Optional[str]
    name: str
    description: Optional[str]

    category_id: Optional[UUID]
    category: Optional[CategoryResponse]
    product_type: str

    uom_id: UUID
    uom: Optional[UOMResponse]
    purchase_uom_id: Optional[UUID]

    standard_cost: float
    list_price: float

    track_inventory: bool
    track_lots: bool
    track_serials: bool
    valuation_method: str

    reorder_point: float
    reorder_quantity: float
    safety_stock: float
    lead_time_days: int

    weight: Optional[float]
    weight_uom: Optional[str]
    dimensions: Optional[dict]

    image_url: Optional[str]

    is_active: bool
    is_purchasable: bool
    is_sellable: bool

    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    # Stock info (optional)
    total_on_hand: Optional[float] = None
    total_available: Optional[float] = None

    class Config:
        from_attributes = True


class ProductSummary(BaseModel):
    id: UUID
    sku: str
    name: str
    barcode: Optional[str]
    category: Optional[str]
    uom: Optional[str]
    list_price: float
    is_active: bool

    class Config:
        from_attributes = True


class ProductFilter(BaseModel):
    search: Optional[str] = None
    category_id: Optional[UUID] = None
    product_type: Optional[ProductTypeEnum] = None
    is_active: Optional[bool] = None
    is_purchasable: Optional[bool] = None
    is_sellable: Optional[bool] = None
    low_stock: Optional[bool] = None  # Below reorder point


class ProductImportRow(BaseModel):
    """For bulk import."""
    sku: str
    name: str
    barcode: Optional[str] = None
    description: Optional[str] = None
    category_code: Optional[str] = None
    uom_code: str = "EA"
    standard_cost: Decimal = Decimal("0")
    list_price: Decimal = Decimal("0")
    reorder_point: Decimal = Decimal("0")
    reorder_quantity: Decimal = Decimal("0")
