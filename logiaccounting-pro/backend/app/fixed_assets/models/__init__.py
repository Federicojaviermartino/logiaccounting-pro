"""
Asset models exports.
"""
from app.fixed_assets.models.category import (
    AssetCategory,
    DepreciationProfile,
    DepreciationMethod,
    PostingFrequency,
)
from app.fixed_assets.models.asset import (
    FixedAsset,
    AssetAttachment,
    AssetStatus,
    AcquisitionType,
    DisposalType,
)
from app.fixed_assets.models.depreciation import (
    DepreciationSchedule,
    DepreciationEntry,
    DepreciationRun,
    DepreciationRunStatus,
    DepreciationEntryStatus,
)
from app.fixed_assets.models.transaction import (
    AssetTransaction,
    TransactionType,
    TransactionStatus,
)
from app.fixed_assets.models.maintenance import (
    AssetMaintenance,
    MaintenanceSchedule,
    MaintenanceType,
    MaintenanceStatus,
)

__all__ = [
    # Category
    "AssetCategory",
    "DepreciationProfile",
    "DepreciationMethod",
    "PostingFrequency",
    # Asset
    "FixedAsset",
    "AssetAttachment",
    "AssetStatus",
    "AcquisitionType",
    "DisposalType",
    # Depreciation
    "DepreciationSchedule",
    "DepreciationEntry",
    "DepreciationRun",
    "DepreciationRunStatus",
    "DepreciationEntryStatus",
    # Transaction
    "AssetTransaction",
    "TransactionType",
    "TransactionStatus",
    # Maintenance
    "AssetMaintenance",
    "MaintenanceSchedule",
    "MaintenanceType",
    "MaintenanceStatus",
]
