"""
API routes for asset category management.
"""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.fixed_assets.models.category import AssetCategory, DepreciationProfile
from app.fixed_assets.schemas.asset import (
    CategoryCreate, CategoryUpdate, CategoryResponse
)

router = APIRouter(prefix="/categories", tags=["Asset Categories"])


@router.get("", response_model=List[CategoryResponse])
async def get_categories(
    parent_id: Optional[UUID] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all asset categories."""
    query = select(AssetCategory).where(
        AssetCategory.customer_id == current_user.customer_id
    )

    if parent_id:
        query = query.where(AssetCategory.parent_id == parent_id)
    else:
        query = query.where(AssetCategory.parent_id == None)

    if active_only:
        query = query.where(AssetCategory.is_active == True)

    query = query.order_by(AssetCategory.code)

    result = db.execute(query)
    categories = result.scalars().all()

    return categories


@router.get("/tree", response_model=List[dict])
async def get_category_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get categories as hierarchical tree."""
    query = select(AssetCategory).where(
        AssetCategory.customer_id == current_user.customer_id,
        AssetCategory.is_active == True
    ).order_by(AssetCategory.level, AssetCategory.code)

    result = db.execute(query)
    categories = result.scalars().all()

    # Build tree structure
    def build_tree(parent_id=None):
        children = []
        for cat in categories:
            if cat.parent_id == parent_id:
                node = {
                    "id": cat.id,
                    "code": cat.code,
                    "name": cat.name,
                    "level": cat.level,
                    "children": build_tree(cat.id)
                }
                children.append(node)
        return children

    return build_tree()


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get category by ID."""
    query = select(AssetCategory).where(
        AssetCategory.id == category_id,
        AssetCategory.customer_id == current_user.customer_id
    )
    result = db.execute(query)
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return category


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new asset category."""
    # Check for duplicate code
    existing = db.execute(
        select(AssetCategory).where(
            AssetCategory.customer_id == current_user.customer_id,
            AssetCategory.code == data.code
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Category code already exists")

    # Determine level
    level = 0
    path = data.code
    if data.parent_id:
        parent = db.get(AssetCategory, data.parent_id)
        if parent:
            level = parent.level + 1
            path = f"{parent.path}/{data.code}"

    category = AssetCategory(
        customer_id=current_user.customer_id,
        code=data.code,
        name=data.name,
        description=data.description,
        parent_id=data.parent_id,
        level=level,
        path=path,
        default_useful_life_months=data.default_useful_life_months,
        default_salvage_percent=data.default_salvage_percent,
        default_depreciation_method=data.default_depreciation_method,
        default_declining_rate=data.default_declining_rate,
        asset_account_id=data.asset_account_id,
        accumulated_depreciation_account_id=data.accumulated_depreciation_account_id,
        depreciation_expense_account_id=data.depreciation_expense_account_id,
        gain_loss_disposal_account_id=data.gain_loss_disposal_account_id,
        capitalize_threshold=data.capitalize_threshold,
        track_maintenance=data.track_maintenance,
        require_serial_number=data.require_serial_number,
        created_by=current_user.id,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update asset category."""
    category = db.execute(
        select(AssetCategory).where(
            AssetCategory.id == category_id,
            AssetCategory.customer_id == current_user.customer_id
        )
    ).scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)

    db.commit()
    db.refresh(category)

    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete asset category (only if no assets)."""
    from app.fixed_assets.models.asset import FixedAsset

    category = db.execute(
        select(AssetCategory).where(
            AssetCategory.id == category_id,
            AssetCategory.customer_id == current_user.customer_id
        )
    ).scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check for assets
    asset_count = db.execute(
        select(func.count(FixedAsset.id)).where(
            FixedAsset.category_id == category_id
        )
    ).scalar()

    if asset_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete category with {asset_count} assets"
        )

    db.delete(category)
    db.commit()


@router.post("/setup-defaults", response_model=dict)
async def setup_default_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Setup default asset categories."""
    from app.fixed_assets.models.category import DepreciationMethod

    defaults = [
        {"code": "LAND", "name": "Land", "useful_life": 0, "method": DepreciationMethod.STRAIGHT_LINE},
        {"code": "BLDG", "name": "Buildings", "useful_life": 480, "method": DepreciationMethod.STRAIGHT_LINE},
        {"code": "MACH", "name": "Machinery & Equipment", "useful_life": 120, "method": DepreciationMethod.STRAIGHT_LINE},
        {"code": "FURN", "name": "Furniture & Fixtures", "useful_life": 84, "method": DepreciationMethod.STRAIGHT_LINE},
        {"code": "VEHI", "name": "Vehicles", "useful_life": 60, "method": DepreciationMethod.DECLINING_BALANCE},
        {"code": "COMP", "name": "Computer Equipment", "useful_life": 36, "method": DepreciationMethod.STRAIGHT_LINE},
        {"code": "SOFT", "name": "Software", "useful_life": 36, "method": DepreciationMethod.STRAIGHT_LINE},
        {"code": "LEAS", "name": "Leasehold Improvements", "useful_life": 120, "method": DepreciationMethod.STRAIGHT_LINE},
    ]

    created = 0
    for item in defaults:
        existing = db.execute(
            select(AssetCategory).where(
                AssetCategory.customer_id == current_user.customer_id,
                AssetCategory.code == item["code"]
            )
        ).scalar_one_or_none()

        if not existing:
            category = AssetCategory(
                customer_id=current_user.customer_id,
                code=item["code"],
                name=item["name"],
                default_useful_life_months=item["useful_life"],
                default_depreciation_method=item["method"],
                default_salvage_percent=0,
                created_by=current_user.id,
            )
            db.add(category)
            created += 1

    db.commit()

    return {"message": f"Created {created} default categories"}
