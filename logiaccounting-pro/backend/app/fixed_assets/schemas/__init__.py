"""
Fixed assets schemas exports.
"""
from app.fixed_assets.schemas.asset import (
    AssetStatus,
    AcquisitionType,
    DepreciationMethod,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryTree,
    AssetCreate,
    AssetUpdate,
    AssetResponse,
    AssetSummary,
    AssetFilter,
    AssetImport,
    BarcodeSearch,
)
from app.fixed_assets.schemas.depreciation import (
    DepreciationScheduleResponse,
    DepreciationRunCreate,
    DepreciationRunResponse,
    DepreciationEntryResponse,
    UnitsOfProductionUpdate,
    UnitsUpdateRequest,
)
from app.fixed_assets.schemas.transaction import (
    DisposalType,
    DisposalCreate,
    TransferCreate,
    RevaluationCreate,
    ImprovementCreate,
    TransactionResponse,
    MovementResponse,
    DisposalResponse,
)

__all__ = [
    # Asset schemas
    "AssetStatus",
    "AcquisitionType",
    "DepreciationMethod",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "CategoryTree",
    "AssetCreate",
    "AssetUpdate",
    "AssetResponse",
    "AssetSummary",
    "AssetFilter",
    "AssetImport",
    "BarcodeSearch",
    # Depreciation schemas
    "DepreciationScheduleResponse",
    "DepreciationRunCreate",
    "DepreciationRunResponse",
    "DepreciationEntryResponse",
    "UnitsOfProductionUpdate",
    "UnitsUpdateRequest",
    # Transaction schemas
    "DisposalType",
    "DisposalCreate",
    "TransferCreate",
    "RevaluationCreate",
    "ImprovementCreate",
    "TransactionResponse",
    "MovementResponse",
    "DisposalResponse",
]
