"""
Products Module
Product and category management
"""

from app.inventory.products.models import (
    Product,
    ProductCategory,
    UnitOfMeasure,
    ProductTypeEnum,
    ValuationMethodEnum,
    UOMCategoryEnum,
)

from app.inventory.products.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductSummary,
    ProductFilter,
    ProductImportRow,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    UOMCreate,
    UOMUpdate,
    UOMResponse,
)

from app.inventory.products.service import (
    ProductService,
    CategoryService,
    UOMService,
    get_product_service,
)


__all__ = [
    # Models
    'Product',
    'ProductCategory',
    'UnitOfMeasure',
    'ProductTypeEnum',
    'ValuationMethodEnum',
    'UOMCategoryEnum',

    # Schemas
    'ProductCreate',
    'ProductUpdate',
    'ProductResponse',
    'ProductSummary',
    'ProductFilter',
    'ProductImportRow',
    'CategoryCreate',
    'CategoryUpdate',
    'CategoryResponse',
    'UOMCreate',
    'UOMUpdate',
    'UOMResponse',

    # Services
    'ProductService',
    'CategoryService',
    'UOMService',
    'get_product_service',
]
