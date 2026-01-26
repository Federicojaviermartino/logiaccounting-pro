"""
Warehouses Module
Warehouse and location management
"""

from app.inventory.warehouses.models import (
    Warehouse,
    WarehouseZone,
    WarehouseLocation,
    LocationTypeEnum,
    ZoneTypeEnum,
)

from app.inventory.warehouses.schemas import (
    WarehouseCreate,
    WarehouseUpdate,
    WarehouseResponse,
    WarehouseSummary,
    ZoneCreate,
    ZoneUpdate,
    ZoneResponse,
    LocationCreate,
    LocationUpdate,
    LocationResponse,
    LocationTreeNode,
    BulkLocationCreate,
    BulkLocationResult,
    AddressSchema,
    CoordinatesSchema,
    LocationCapacity,
)

from app.inventory.warehouses.service import (
    WarehouseService,
    get_warehouse_service,
)


__all__ = [
    # Models
    'Warehouse',
    'WarehouseZone',
    'WarehouseLocation',
    'LocationTypeEnum',
    'ZoneTypeEnum',

    # Schemas
    'WarehouseCreate',
    'WarehouseUpdate',
    'WarehouseResponse',
    'WarehouseSummary',
    'ZoneCreate',
    'ZoneUpdate',
    'ZoneResponse',
    'LocationCreate',
    'LocationUpdate',
    'LocationResponse',
    'LocationTreeNode',
    'BulkLocationCreate',
    'BulkLocationResult',
    'AddressSchema',
    'CoordinatesSchema',
    'LocationCapacity',

    # Services
    'WarehouseService',
    'get_warehouse_service',
]
