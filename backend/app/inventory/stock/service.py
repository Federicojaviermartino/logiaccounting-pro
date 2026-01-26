"""
Stock Service
Business logic for stock levels and tracking
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple, Dict
from uuid import UUID
import logging

from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session, joinedload

from app.inventory.stock.models import (
    StockLevel, StockLot, StockSerial, StockValuationLayer,
    LotStatusEnum, SerialStatusEnum
)
from app.inventory.stock.schemas import (
    LotCreate, LotUpdate, LotFilter,
    SerialCreate, SerialUpdate, SerialFilter, BulkSerialCreate,
    StockFilter, StockReservation, StockReservationResult,
)
from app.inventory.products.models import Product
from app.inventory.warehouses.models import Warehouse, WarehouseLocation

logger = logging.getLogger(__name__)


class LotService:
    """Service for lot management."""

    def __init__(self, db: Session):
        self.db = db

    def create_lot(
        self,
        customer_id: UUID,
        data: LotCreate,
        created_by: UUID = None,
    ) -> StockLot:
        """Create a new lot."""
        # Check for duplicate
        existing = self.db.query(StockLot).filter(
            StockLot.customer_id == customer_id,
            StockLot.product_id == data.product_id,
            StockLot.lot_number == data.lot_number
        ).first()

        if existing:
            raise ValueError(f"Lot '{data.lot_number}' already exists for this product")

        lot = StockLot(
            customer_id=customer_id,
            product_id=data.product_id,
            lot_number=data.lot_number,
            manufacture_date=data.manufacture_date,
            expiry_date=data.expiry_date,
            supplier_id=data.supplier_id,
            supplier_lot=data.supplier_lot,
            notes=data.notes,
            created_by=created_by,
        )

        self.db.add(lot)
        self.db.commit()
        self.db.refresh(lot)

        return lot

    def get_lot_by_id(self, lot_id: UUID) -> Optional[StockLot]:
        """Get lot by ID."""
        return self.db.query(StockLot).get(lot_id)

    def get_lot_by_number(
        self,
        customer_id: UUID,
        product_id: UUID,
        lot_number: str,
    ) -> Optional[StockLot]:
        """Get lot by number."""
        return self.db.query(StockLot).filter(
            StockLot.customer_id == customer_id,
            StockLot.product_id == product_id,
            StockLot.lot_number == lot_number
        ).first()

    def get_lots(
        self,
        customer_id: UUID,
        filters: LotFilter = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[StockLot], int]:
        """Get lots with filtering."""
        query = self.db.query(StockLot).filter(
            StockLot.customer_id == customer_id
        )

        if filters:
            if filters.product_id:
                query = query.filter(StockLot.product_id == filters.product_id)

            if filters.status:
                query = query.filter(StockLot.status == filters.status.value)

            if filters.expiring_within_days:
                expiry_date = date.today() + timedelta(days=filters.expiring_within_days)
                query = query.filter(
                    StockLot.expiry_date != None,
                    StockLot.expiry_date <= expiry_date,
                    StockLot.expiry_date >= date.today()
                )

            if filters.expired:
                query = query.filter(
                    StockLot.expiry_date != None,
                    StockLot.expiry_date < date.today()
                )

        total = query.count()
        lots = query.order_by(
            StockLot.expiry_date.nullslast(),
            StockLot.lot_number
        ).offset((page - 1) * page_size).limit(page_size).all()

        return lots, total

    def update_lot(self, lot_id: UUID, data: LotUpdate) -> StockLot:
        """Update a lot."""
        lot = self.get_lot_by_id(lot_id)
        if not lot:
            raise ValueError("Lot not found")

        for key, value in data.dict(exclude_unset=True).items():
            if value is not None:
                if key == "status":
                    value = value.value
                setattr(lot, key, value)

        self.db.commit()
        self.db.refresh(lot)

        return lot

    def get_expiring_lots(
        self,
        customer_id: UUID,
        days_ahead: int = 30,
    ) -> List[StockLot]:
        """Get lots expiring soon."""
        expiry_date = date.today() + timedelta(days=days_ahead)

        return self.db.query(StockLot).filter(
            StockLot.customer_id == customer_id,
            StockLot.status == LotStatusEnum.AVAILABLE.value,
            StockLot.expiry_date != None,
            StockLot.expiry_date <= expiry_date,
            StockLot.expiry_date >= date.today()
        ).order_by(StockLot.expiry_date).all()


class SerialService:
    """Service for serial number management."""

    def __init__(self, db: Session):
        self.db = db

    def create_serial(
        self,
        customer_id: UUID,
        data: SerialCreate,
        created_by: UUID = None,
    ) -> StockSerial:
        """Create a serial number."""
        # Check for duplicate
        existing = self.db.query(StockSerial).filter(
            StockSerial.customer_id == customer_id,
            StockSerial.product_id == data.product_id,
            StockSerial.serial_number == data.serial_number
        ).first()

        if existing:
            raise ValueError(f"Serial '{data.serial_number}' already exists for this product")

        serial = StockSerial(
            customer_id=customer_id,
            product_id=data.product_id,
            serial_number=data.serial_number,
            lot_id=data.lot_id,
            warehouse_id=data.warehouse_id,
            location_id=data.location_id,
            warranty_start=data.warranty_start,
            warranty_end=data.warranty_end,
            notes=data.notes,
            created_by=created_by,
        )

        self.db.add(serial)
        self.db.commit()
        self.db.refresh(serial)

        return serial

    def bulk_create_serials(
        self,
        customer_id: UUID,
        data: BulkSerialCreate,
        created_by: UUID = None,
    ) -> dict:
        """Create multiple serials."""
        created = 0
        errors = []

        serial_numbers = data.serial_numbers if data.serial_numbers else []

        # Generate from pattern
        if data.prefix and data.start_number and data.count:
            for i in range(data.count):
                serial_numbers.append(f"{data.prefix}{data.start_number + i:06d}")

        for sn in serial_numbers:
            try:
                # Check duplicate
                existing = self.db.query(StockSerial).filter(
                    StockSerial.customer_id == customer_id,
                    StockSerial.product_id == data.product_id,
                    StockSerial.serial_number == sn
                ).first()

                if existing:
                    errors.append({"serial": sn, "error": "Already exists"})
                    continue

                serial = StockSerial(
                    customer_id=customer_id,
                    product_id=data.product_id,
                    serial_number=sn,
                    lot_id=data.lot_id,
                    warehouse_id=data.warehouse_id,
                    location_id=data.location_id,
                    warranty_start=data.warranty_start,
                    warranty_end=data.warranty_end,
                    created_by=created_by,
                )
                self.db.add(serial)
                created += 1

            except Exception as e:
                errors.append({"serial": sn, "error": str(e)})

        self.db.commit()

        return {
            "created": created,
            "errors": errors,
        }

    def get_serial_by_number(
        self,
        customer_id: UUID,
        product_id: UUID,
        serial_number: str,
    ) -> Optional[StockSerial]:
        """Get serial by number."""
        return self.db.query(StockSerial).filter(
            StockSerial.customer_id == customer_id,
            StockSerial.product_id == product_id,
            StockSerial.serial_number == serial_number
        ).first()

    def get_serials(
        self,
        customer_id: UUID,
        filters: SerialFilter = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[StockSerial], int]:
        """Get serials with filtering."""
        query = self.db.query(StockSerial).filter(
            StockSerial.customer_id == customer_id
        )

        if filters:
            if filters.product_id:
                query = query.filter(StockSerial.product_id == filters.product_id)

            if filters.lot_id:
                query = query.filter(StockSerial.lot_id == filters.lot_id)

            if filters.warehouse_id:
                query = query.filter(StockSerial.warehouse_id == filters.warehouse_id)

            if filters.status:
                query = query.filter(StockSerial.status == filters.status.value)

            if filters.search:
                query = query.filter(
                    StockSerial.serial_number.ilike(f"%{filters.search}%")
                )

        total = query.count()
        serials = query.options(
            joinedload(StockSerial.lot)
        ).order_by(
            StockSerial.serial_number
        ).offset((page - 1) * page_size).limit(page_size).all()

        return serials, total

    def update_serial(self, serial_id: UUID, data: SerialUpdate) -> StockSerial:
        """Update a serial."""
        serial = self.db.query(StockSerial).get(serial_id)
        if not serial:
            raise ValueError("Serial not found")

        for key, value in data.dict(exclude_unset=True).items():
            if value is not None:
                if key == "status":
                    value = value.value
                setattr(serial, key, value)

        self.db.commit()
        self.db.refresh(serial)

        return serial


class StockService:
    """Service for stock level management."""

    def __init__(self, db: Session):
        self.db = db
        self.lot_service = LotService(db)
        self.serial_service = SerialService(db)

    def get_stock_level(
        self,
        customer_id: UUID,
        product_id: UUID,
        warehouse_id: UUID,
        location_id: UUID,
        lot_id: UUID = None,
    ) -> Optional[StockLevel]:
        """Get specific stock level."""
        return self.db.query(StockLevel).filter(
            StockLevel.customer_id == customer_id,
            StockLevel.product_id == product_id,
            StockLevel.warehouse_id == warehouse_id,
            StockLevel.location_id == location_id,
            StockLevel.lot_id == lot_id
        ).first()

    def get_or_create_stock_level(
        self,
        customer_id: UUID,
        product_id: UUID,
        warehouse_id: UUID,
        location_id: UUID,
        lot_id: UUID = None,
    ) -> StockLevel:
        """Get or create stock level record."""
        stock = self.get_stock_level(
            customer_id, product_id, warehouse_id, location_id, lot_id
        )

        if not stock:
            stock = StockLevel(
                customer_id=customer_id,
                product_id=product_id,
                warehouse_id=warehouse_id,
                location_id=location_id,
                lot_id=lot_id,
                quantity_on_hand=Decimal("0"),
                quantity_reserved=Decimal("0"),
            )
            self.db.add(stock)
            self.db.flush()

        return stock

    def get_stock_levels(
        self,
        customer_id: UUID,
        filters: StockFilter = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[StockLevel], int]:
        """Get stock levels with filtering."""
        query = self.db.query(StockLevel).filter(
            StockLevel.customer_id == customer_id
        )

        if filters:
            if filters.product_id:
                query = query.filter(StockLevel.product_id == filters.product_id)

            if filters.warehouse_id:
                query = query.filter(StockLevel.warehouse_id == filters.warehouse_id)

            if filters.location_id:
                query = query.filter(StockLevel.location_id == filters.location_id)

            if filters.lot_id:
                query = query.filter(StockLevel.lot_id == filters.lot_id)

            if filters.has_stock_only:
                query = query.filter(StockLevel.quantity_on_hand > 0)

            if filters.search:
                query = query.join(Product).filter(
                    or_(
                        Product.sku.ilike(f"%{filters.search}%"),
                        Product.name.ilike(f"%{filters.search}%"),
                    )
                )

        total = query.count()

        stocks = query.options(
            joinedload(StockLevel.product),
            joinedload(StockLevel.warehouse),
            joinedload(StockLevel.location),
            joinedload(StockLevel.lot),
        ).order_by(
            StockLevel.product_id,
            StockLevel.warehouse_id,
            StockLevel.location_id
        ).offset((page - 1) * page_size).limit(page_size).all()

        return stocks, total

    def get_product_stock_summary(
        self,
        customer_id: UUID,
        product_id: UUID,
    ) -> dict:
        """Get stock summary for a product across all locations."""
        stock_levels = self.db.query(StockLevel).filter(
            StockLevel.customer_id == customer_id,
            StockLevel.product_id == product_id
        ).options(
            joinedload(StockLevel.warehouse),
            joinedload(StockLevel.location),
        ).all()

        total_on_hand = sum(s.quantity_on_hand for s in stock_levels)
        total_reserved = sum(s.quantity_reserved for s in stock_levels)
        total_value = sum(s.total_value or 0 for s in stock_levels)

        # Group by warehouse
        by_warehouse = {}
        for stock in stock_levels:
            wh_id = str(stock.warehouse_id)
            if wh_id not in by_warehouse:
                by_warehouse[wh_id] = {
                    "warehouse_id": wh_id,
                    "warehouse_code": stock.warehouse.code,
                    "quantity_on_hand": 0,
                    "quantity_reserved": 0,
                    "quantity_available": 0,
                    "locations": [],
                }
            by_warehouse[wh_id]["quantity_on_hand"] += float(stock.quantity_on_hand)
            by_warehouse[wh_id]["quantity_reserved"] += float(stock.quantity_reserved)
            by_warehouse[wh_id]["quantity_available"] += float(stock.quantity_available or (stock.quantity_on_hand - stock.quantity_reserved))
            by_warehouse[wh_id]["locations"].append({
                "location_code": stock.location.code,
                "quantity": float(stock.quantity_on_hand),
            })

        product = self.db.query(Product).get(product_id)

        return {
            "product_id": str(product_id),
            "product_sku": product.sku if product else None,
            "product_name": product.name if product else None,
            "total_on_hand": float(total_on_hand),
            "total_reserved": float(total_reserved),
            "total_available": float(total_on_hand - total_reserved),
            "total_value": float(total_value),
            "reorder_point": float(product.reorder_point) if product else 0,
            "is_low_stock": float(total_on_hand - total_reserved) <= float(product.reorder_point) if product else False,
            "by_warehouse": list(by_warehouse.values()),
        }

    def get_low_stock_products(
        self,
        customer_id: UUID,
        warehouse_id: UUID = None,
    ) -> List[dict]:
        """Get products below reorder point."""
        # Aggregate stock by product
        query = self.db.query(
            StockLevel.product_id,
            func.sum(StockLevel.quantity_on_hand - StockLevel.quantity_reserved).label("available")
        ).filter(
            StockLevel.customer_id == customer_id
        )

        if warehouse_id:
            query = query.filter(StockLevel.warehouse_id == warehouse_id)

        query = query.group_by(StockLevel.product_id)

        # Join with products to get reorder point
        stock_data = query.all()

        low_stock = []
        for product_id, available in stock_data:
            product = self.db.query(Product).get(product_id)
            if product and float(available or 0) <= float(product.reorder_point):
                low_stock.append({
                    "product_id": str(product_id),
                    "product_sku": product.sku,
                    "product_name": product.name,
                    "quantity_available": float(available or 0),
                    "reorder_point": float(product.reorder_point),
                    "reorder_quantity": float(product.reorder_quantity),
                    "shortage": float(product.reorder_point) - float(available or 0),
                })

        return sorted(low_stock, key=lambda x: x["shortage"], reverse=True)

    def reserve_stock(
        self,
        customer_id: UUID,
        reservation: StockReservation,
    ) -> StockReservationResult:
        """Reserve stock for an order."""
        # Find available stock
        query = self.db.query(StockLevel).filter(
            StockLevel.customer_id == customer_id,
            StockLevel.product_id == reservation.product_id,
            StockLevel.warehouse_id == reservation.warehouse_id,
            (StockLevel.quantity_on_hand - StockLevel.quantity_reserved) > 0
        )

        if reservation.lot_id:
            query = query.filter(StockLevel.lot_id == reservation.lot_id)

        # Order by FIFO (oldest first based on lot or movement date)
        stock_levels = query.order_by(
            StockLevel.last_movement_date.nullslast()
        ).all()

        remaining = reservation.quantity
        reservations = []

        for stock in stock_levels:
            if remaining <= 0:
                break

            available = Decimal(str(stock.quantity_on_hand)) - Decimal(str(stock.quantity_reserved))
            to_reserve = min(remaining, available)

            stock.quantity_reserved += to_reserve
            remaining -= to_reserve

            reservations.append({
                "stock_level_id": str(stock.id),
                "location_id": str(stock.location_id),
                "lot_id": str(stock.lot_id) if stock.lot_id else None,
                "quantity_reserved": float(to_reserve),
            })

        self.db.commit()

        return StockReservationResult(
            success=remaining == 0,
            reserved_quantity=float(reservation.quantity - remaining),
            remaining_quantity=float(remaining),
            reservations=reservations,
            message=None if remaining == 0 else f"Only {float(reservation.quantity - remaining)} available",
        )

    def release_reservation(
        self,
        stock_level_id: UUID,
        quantity: Decimal,
    ) -> StockLevel:
        """Release reserved stock."""
        stock = self.db.query(StockLevel).get(stock_level_id)
        if not stock:
            raise ValueError("Stock level not found")

        if quantity > stock.quantity_reserved:
            raise ValueError("Cannot release more than reserved")

        stock.quantity_reserved -= quantity
        self.db.commit()
        self.db.refresh(stock)

        return stock


def get_stock_service(db: Session) -> StockService:
    """Factory function."""
    return StockService(db)
