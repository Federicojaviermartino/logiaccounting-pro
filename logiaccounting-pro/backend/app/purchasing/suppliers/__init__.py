"""
Suppliers Module
Supplier management
"""

from app.purchasing.suppliers.models import (
    Supplier,
    SupplierContact,
    SupplierPriceList,
    SupplierTypeEnum,
)

from app.purchasing.suppliers.schemas import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierFilter,
    SupplierSummary,
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    PriceListCreate,
    PriceListUpdate,
    PriceListResponse,
    AddressSchema,
    SupplierApproval,
)

from app.purchasing.suppliers.service import (
    SupplierService,
    get_supplier_service,
)


__all__ = [
    # Models
    'Supplier',
    'SupplierContact',
    'SupplierPriceList',
    'SupplierTypeEnum',

    # Schemas
    'SupplierCreate',
    'SupplierUpdate',
    'SupplierResponse',
    'SupplierFilter',
    'SupplierSummary',
    'ContactCreate',
    'ContactUpdate',
    'ContactResponse',
    'PriceListCreate',
    'PriceListUpdate',
    'PriceListResponse',
    'AddressSchema',
    'SupplierApproval',

    # Services
    'SupplierService',
    'get_supplier_service',
]
