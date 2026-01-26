"""
Stock Module
Stock levels, lots, and serial tracking
"""

from app.inventory.stock.models import (
    StockLevel,
    StockLot,
    StockSerial,
    StockValuationLayer,
    LotStatusEnum,
    SerialStatusEnum,
)

from app.inventory.stock.schemas import (
    LotCreate,
    LotUpdate,
    LotResponse,
    LotFilter,
    SerialCreate,
    SerialUpdate,
    SerialResponse,
    SerialFilter,
    BulkSerialCreate,
    StockLevelResponse,
    StockSummaryByProduct,
    StockSummaryByWarehouse,
    StockFilter,
    StockReservation,
    StockReservationResult,
    StockValuationReport,
)

from app.inventory.stock.service import (
    StockService,
    LotService,
    SerialService,
    get_stock_service,
)


__all__ = [
    # Models
    'StockLevel',
    'StockLot',
    'StockSerial',
    'StockValuationLayer',
    'LotStatusEnum',
    'SerialStatusEnum',

    # Schemas
    'LotCreate',
    'LotUpdate',
    'LotResponse',
    'LotFilter',
    'SerialCreate',
    'SerialUpdate',
    'SerialResponse',
    'SerialFilter',
    'BulkSerialCreate',
    'StockLevelResponse',
    'StockSummaryByProduct',
    'StockSummaryByWarehouse',
    'StockFilter',
    'StockReservation',
    'StockReservationResult',
    'StockValuationReport',

    # Services
    'StockService',
    'LotService',
    'SerialService',
    'get_stock_service',
]
