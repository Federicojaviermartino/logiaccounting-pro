"""
Product Service
Business logic for products and categories
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload

from app.inventory.products.models import (
    Product, ProductCategory, UnitOfMeasure,
    ProductTypeEnum, ValuationMethodEnum
)
from app.inventory.products.schemas import (
    ProductCreate, ProductUpdate, ProductFilter,
    CategoryCreate, CategoryUpdate,
    UOMCreate, UOMUpdate,
    ProductImportRow,
)

logger = logging.getLogger(__name__)


class UOMService:
    """Service for units of measure."""

    def __init__(self, db: Session):
        self.db = db

    def create_uom(
        self,
        customer_id: UUID,
        data: UOMCreate,
    ) -> UnitOfMeasure:
        """Create a unit of measure."""
        # Check for duplicate code
        existing = self.db.query(UnitOfMeasure).filter(
            UnitOfMeasure.customer_id == customer_id,
            UnitOfMeasure.code == data.code.upper()
        ).first()

        if existing:
            raise ValueError(f"UOM code '{data.code}' already exists")

        uom = UnitOfMeasure(
            customer_id=customer_id,
            code=data.code.upper(),
            name=data.name,
            category=data.category.value if data.category else None,
            base_uom_id=data.base_uom_id,
            conversion_factor=data.conversion_factor,
        )

        self.db.add(uom)
        self.db.commit()
        self.db.refresh(uom)

        return uom

    def get_uoms(
        self,
        customer_id: UUID,
        category: str = None,
        active_only: bool = True,
    ) -> List[UnitOfMeasure]:
        """Get units of measure."""
        query = self.db.query(UnitOfMeasure).filter(
            UnitOfMeasure.customer_id == customer_id
        )

        if active_only:
            query = query.filter(UnitOfMeasure.is_active == True)

        if category:
            query = query.filter(UnitOfMeasure.category == category)

        return query.order_by(UnitOfMeasure.code).all()

    def get_uom_by_code(self, customer_id: UUID, code: str) -> Optional[UnitOfMeasure]:
        """Get UOM by code."""
        return self.db.query(UnitOfMeasure).filter(
            UnitOfMeasure.customer_id == customer_id,
            UnitOfMeasure.code == code.upper()
        ).first()

    def seed_default_uoms(self, customer_id: UUID) -> List[UnitOfMeasure]:
        """Create default UOMs for a customer."""
        defaults = [
            ("EA", "Each", "unit", None, 1),
            ("PC", "Piece", "unit", None, 1),
            ("BOX", "Box", "unit", None, 1),
            ("KG", "Kilogram", "weight", None, 1),
            ("G", "Gram", "weight", "KG", 0.001),
            ("LB", "Pound", "weight", "KG", 0.453592),
            ("L", "Liter", "volume", None, 1),
            ("ML", "Milliliter", "volume", "L", 0.001),
            ("M", "Meter", "length", None, 1),
            ("CM", "Centimeter", "length", "M", 0.01),
            ("HR", "Hour", "time", None, 1),
        ]

        created = []
        base_uoms = {}

        # First pass: create base UOMs
        for code, name, category, base_code, factor in defaults:
            if base_code is None:
                uom = UnitOfMeasure(
                    customer_id=customer_id,
                    code=code,
                    name=name,
                    category=category,
                    conversion_factor=factor,
                )
                self.db.add(uom)
                self.db.flush()
                base_uoms[code] = uom.id
                created.append(uom)

        # Second pass: create derived UOMs
        for code, name, category, base_code, factor in defaults:
            if base_code is not None:
                uom = UnitOfMeasure(
                    customer_id=customer_id,
                    code=code,
                    name=name,
                    category=category,
                    base_uom_id=base_uoms.get(base_code),
                    conversion_factor=factor,
                )
                self.db.add(uom)
                created.append(uom)

        self.db.commit()
        return created


class CategoryService:
    """Service for product categories."""

    def __init__(self, db: Session):
        self.db = db

    def create_category(
        self,
        customer_id: UUID,
        data: CategoryCreate,
    ) -> ProductCategory:
        """Create a product category."""
        # Check for duplicate code
        existing = self.db.query(ProductCategory).filter(
            ProductCategory.customer_id == customer_id,
            ProductCategory.code == data.code.upper()
        ).first()

        if existing:
            raise ValueError(f"Category code '{data.code}' already exists")

        # Get parent info
        level = 0
        path = "/"

        if data.parent_id:
            parent = self.db.query(ProductCategory).get(data.parent_id)
            if parent:
                level = parent.level + 1
                path = f"{parent.path}{parent.id}/"

        category = ProductCategory(
            customer_id=customer_id,
            code=data.code.upper(),
            name=data.name,
            description=data.description,
            parent_id=data.parent_id,
            level=level,
            path=path,
            default_uom_id=data.default_uom_id,
            default_valuation_method=data.default_valuation_method.value,
        )

        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)

        return category

    def get_categories(
        self,
        customer_id: UUID,
        parent_id: UUID = None,
        active_only: bool = True,
    ) -> List[ProductCategory]:
        """Get categories."""
        query = self.db.query(ProductCategory).filter(
            ProductCategory.customer_id == customer_id
        )

        if active_only:
            query = query.filter(ProductCategory.is_active == True)

        if parent_id:
            query = query.filter(ProductCategory.parent_id == parent_id)

        return query.order_by(ProductCategory.code).all()

    def get_category_tree(
        self,
        customer_id: UUID,
        active_only: bool = True,
    ) -> List[ProductCategory]:
        """Get categories as hierarchical tree."""
        query = self.db.query(ProductCategory).filter(
            ProductCategory.customer_id == customer_id,
            ProductCategory.parent_id == None
        )

        if active_only:
            query = query.filter(ProductCategory.is_active == True)

        return query.options(
            joinedload(ProductCategory.children)
        ).order_by(ProductCategory.code).all()

    def get_category_by_code(
        self,
        customer_id: UUID,
        code: str
    ) -> Optional[ProductCategory]:
        """Get category by code."""
        return self.db.query(ProductCategory).filter(
            ProductCategory.customer_id == customer_id,
            ProductCategory.code == code.upper()
        ).first()

    def update_category(
        self,
        category_id: UUID,
        data: CategoryUpdate,
    ) -> ProductCategory:
        """Update a category."""
        category = self.db.query(ProductCategory).get(category_id)
        if not category:
            raise ValueError("Category not found")

        for key, value in data.dict(exclude_unset=True).items():
            if value is not None:
                if key == "default_valuation_method":
                    value = value.value
                setattr(category, key, value)

        self.db.commit()
        self.db.refresh(category)

        return category


class ProductService:
    """Service for products."""

    def __init__(self, db: Session):
        self.db = db
        self.uom_service = UOMService(db)
        self.category_service = CategoryService(db)

    def create_product(
        self,
        customer_id: UUID,
        data: ProductCreate,
        created_by: UUID = None,
    ) -> Product:
        """Create a product."""
        # Check for duplicate SKU
        existing = self.db.query(Product).filter(
            Product.customer_id == customer_id,
            Product.sku == data.sku.upper()
        ).first()

        if existing:
            raise ValueError(f"Product SKU '{data.sku}' already exists")

        # Check barcode uniqueness
        if data.barcode:
            existing_barcode = self.db.query(Product).filter(
                Product.customer_id == customer_id,
                Product.barcode == data.barcode
            ).first()
            if existing_barcode:
                raise ValueError(f"Barcode '{data.barcode}' already in use")

        product = Product(
            customer_id=customer_id,
            sku=data.sku.upper(),
            barcode=data.barcode,
            name=data.name,
            description=data.description,
            category_id=data.category_id,
            product_type=data.product_type.value,
            uom_id=data.uom_id,
            purchase_uom_id=data.purchase_uom_id,
            standard_cost=data.standard_cost,
            list_price=data.list_price,
            track_inventory=data.track_inventory,
            track_lots=data.track_lots,
            track_serials=data.track_serials,
            valuation_method=data.valuation_method.value,
            reorder_point=data.reorder_point,
            reorder_quantity=data.reorder_quantity,
            safety_stock=data.safety_stock,
            lead_time_days=data.lead_time_days,
            weight=data.weight,
            weight_uom=data.weight_uom,
            inventory_account_id=data.inventory_account_id,
            cogs_account_id=data.cogs_account_id,
            revenue_account_id=data.revenue_account_id,
            image_url=data.image_url,
            is_purchasable=data.is_purchasable,
            is_sellable=data.is_sellable,
            created_by=created_by,
        )

        # Handle dimensions
        if data.dimensions:
            product.length = data.dimensions.length
            product.width = data.dimensions.width
            product.height = data.dimensions.height
            product.dimension_uom = data.dimensions.uom

        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)

        logger.info(f"Created product: {product.sku}")
        return product

    def get_product_by_id(self, product_id: UUID) -> Optional[Product]:
        """Get product by ID."""
        return self.db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.uom),
            joinedload(Product.purchase_uom),
        ).get(product_id)

    def get_product_by_sku(
        self,
        customer_id: UUID,
        sku: str
    ) -> Optional[Product]:
        """Get product by SKU."""
        return self.db.query(Product).filter(
            Product.customer_id == customer_id,
            Product.sku == sku.upper()
        ).first()

    def get_product_by_barcode(
        self,
        customer_id: UUID,
        barcode: str
    ) -> Optional[Product]:
        """Get product by barcode."""
        return self.db.query(Product).filter(
            Product.customer_id == customer_id,
            Product.barcode == barcode
        ).first()

    def get_products(
        self,
        customer_id: UUID,
        filters: ProductFilter = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Product], int]:
        """Get products with filtering."""
        query = self.db.query(Product).filter(
            Product.customer_id == customer_id
        ).options(
            joinedload(Product.category),
            joinedload(Product.uom),
        )

        if filters:
            if filters.search:
                search = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Product.sku.ilike(search),
                        Product.name.ilike(search),
                        Product.barcode.ilike(search),
                    )
                )

            if filters.category_id:
                query = query.filter(Product.category_id == filters.category_id)

            if filters.product_type:
                query = query.filter(Product.product_type == filters.product_type.value)

            if filters.is_active is not None:
                query = query.filter(Product.is_active == filters.is_active)

            if filters.is_purchasable is not None:
                query = query.filter(Product.is_purchasable == filters.is_purchasable)

            if filters.is_sellable is not None:
                query = query.filter(Product.is_sellable == filters.is_sellable)

        # Get total
        total = query.count()

        # Paginate
        products = query.order_by(Product.sku).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return products, total

    def update_product(
        self,
        product_id: UUID,
        data: ProductUpdate,
    ) -> Product:
        """Update a product."""
        product = self.get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")

        update_data = data.dict(exclude_unset=True)

        # Handle dimensions
        if "dimensions" in update_data and update_data["dimensions"]:
            dims = update_data.pop("dimensions")
            product.length = dims.get("length")
            product.width = dims.get("width")
            product.height = dims.get("height")
            product.dimension_uom = dims.get("uom")

        for key, value in update_data.items():
            if hasattr(product, key):
                setattr(product, key, value)

        product.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(product)

        return product

    def deactivate_product(self, product_id: UUID) -> Product:
        """Deactivate a product."""
        product = self.get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")

        # Check if product has stock
        from app.inventory.stock.models import StockLevel
        stock = self.db.query(StockLevel).filter(
            StockLevel.product_id == product_id,
            StockLevel.quantity_on_hand > 0
        ).first()

        if stock:
            raise ValueError("Cannot deactivate product with stock on hand")

        product.is_active = False
        product.updated_at = datetime.utcnow()
        self.db.commit()

        return product

    def bulk_import_products(
        self,
        customer_id: UUID,
        products: List[ProductImportRow],
        created_by: UUID = None,
    ) -> dict:
        """Bulk import products."""
        created = 0
        updated = 0
        errors = []

        for i, row in enumerate(products):
            try:
                # Get or create UOM
                uom = self.uom_service.get_uom_by_code(customer_id, row.uom_code)
                if not uom:
                    raise ValueError(f"UOM '{row.uom_code}' not found")

                # Get category if specified
                category_id = None
                if row.category_code:
                    category = self.category_service.get_category_by_code(
                        customer_id, row.category_code
                    )
                    if category:
                        category_id = category.id

                # Check if exists
                existing = self.get_product_by_sku(customer_id, row.sku)

                if existing:
                    # Update
                    existing.name = row.name
                    existing.barcode = row.barcode
                    existing.description = row.description
                    existing.standard_cost = row.standard_cost
                    existing.list_price = row.list_price
                    existing.reorder_point = row.reorder_point
                    existing.reorder_quantity = row.reorder_quantity
                    if category_id:
                        existing.category_id = category_id
                    updated += 1
                else:
                    # Create
                    product = Product(
                        customer_id=customer_id,
                        sku=row.sku.upper(),
                        barcode=row.barcode,
                        name=row.name,
                        description=row.description,
                        category_id=category_id,
                        uom_id=uom.id,
                        standard_cost=row.standard_cost,
                        list_price=row.list_price,
                        reorder_point=row.reorder_point,
                        reorder_quantity=row.reorder_quantity,
                        created_by=created_by,
                    )
                    self.db.add(product)
                    created += 1

            except Exception as e:
                errors.append({
                    "row": i + 1,
                    "sku": row.sku,
                    "error": str(e),
                })

        self.db.commit()

        return {
            "created": created,
            "updated": updated,
            "errors": errors,
            "total_processed": len(products),
        }


def get_product_service(db: Session) -> ProductService:
    """Factory function."""
    return ProductService(db)
