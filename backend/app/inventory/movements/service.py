"""Movement Service - Business logic for stock movements"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy.orm import Session, joinedload

from app.inventory.movements.models import StockMovement, MovementTypeEnum, MovementStatusEnum
from app.inventory.movements.schemas import (
    ReceiptCreate, IssueCreate, TransferCreate, AdjustmentCreate, MovementFilter
)
from app.inventory.stock.models import StockLevel, StockValuationLayer
from app.inventory.stock.service import StockService, LotService
from app.inventory.products.models import Product
from app.inventory.warehouses.models import WarehouseLocation

logger = logging.getLogger(__name__)


class MovementService:
    def __init__(self, db: Session):
        self.db = db
        self.stock_service = StockService(db)
        self.lot_service = LotService(db)

    def _generate_number(self, customer_id: UUID, prefix: str) -> str:
        date_str = datetime.utcnow().strftime("%Y%m")
        last = self.db.query(StockMovement).filter(
            StockMovement.customer_id == customer_id,
            StockMovement.movement_number.like(f"{prefix}-{date_str}-%")
        ).order_by(StockMovement.movement_number.desc()).first()
        seq = int(last.movement_number.split("-")[-1]) + 1 if last else 1
        return f"{prefix}-{date_str}-{seq:05d}"

    def create_receipt(self, customer_id: UUID, data: ReceiptCreate, created_by: UUID = None) -> StockMovement:
        product = self.db.query(Product).get(data.product_id)
        if not product or not product.track_inventory:
            raise ValueError("Invalid product")

        location = self.db.query(WarehouseLocation).get(data.location_id)
        if not location or not location.is_receivable:
            raise ValueError("Invalid location")

        lot_id = data.lot_id
        if product.track_lots and data.lot_number and not lot_id:
            from app.inventory.stock.schemas import LotCreate
            lot = self.lot_service.create_lot(customer_id, LotCreate(
                product_id=data.product_id, lot_number=data.lot_number,
                expiry_date=data.lot_expiry_date.date() if data.lot_expiry_date else None
            ), created_by)
            lot_id = lot.id

        movement = StockMovement(
            customer_id=customer_id,
            movement_number=self._generate_number(customer_id, "RCV"),
            movement_type=MovementTypeEnum.RECEIPT.value,
            movement_date=data.movement_date or datetime.utcnow(),
            product_id=data.product_id,
            lot_id=lot_id,
            dest_warehouse_id=data.warehouse_id,
            dest_location_id=data.location_id,
            quantity=data.quantity,
            uom_id=product.uom_id,
            unit_cost=data.unit_cost,
            total_cost=data.quantity * data.unit_cost,
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            reference_number=data.reference_number,
            status=MovementStatusEnum.DRAFT.value,
            notes=data.notes,
            created_by=created_by,
        )
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(movement)
        return movement

    def create_issue(self, customer_id: UUID, data: IssueCreate, created_by: UUID = None) -> StockMovement:
        product = self.db.query(Product).get(data.product_id)
        if not product:
            raise ValueError("Product not found")

        stock = self.stock_service.get_stock_level(
            customer_id, data.product_id, data.warehouse_id, data.location_id, data.lot_id
        )
        if not stock:
            raise ValueError("No stock at location")

        available = Decimal(str(stock.quantity_on_hand)) - Decimal(str(stock.quantity_reserved))
        if data.quantity > available:
            raise ValueError(f"Insufficient stock. Available: {available}")

        movement = StockMovement(
            customer_id=customer_id,
            movement_number=self._generate_number(customer_id, "ISS"),
            movement_type=MovementTypeEnum.ISSUE.value,
            movement_date=data.movement_date or datetime.utcnow(),
            product_id=data.product_id,
            lot_id=data.lot_id,
            source_warehouse_id=data.warehouse_id,
            source_location_id=data.location_id,
            quantity=data.quantity,
            uom_id=product.uom_id,
            unit_cost=stock.unit_cost or Decimal("0"),
            total_cost=data.quantity * (stock.unit_cost or Decimal("0")),
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            reference_number=data.reference_number,
            status=MovementStatusEnum.DRAFT.value,
            reason=data.reason,
            notes=data.notes,
            created_by=created_by,
        )
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(movement)
        return movement

    def create_transfer(self, customer_id: UUID, data: TransferCreate, created_by: UUID = None) -> StockMovement:
        product = self.db.query(Product).get(data.product_id)
        if not product:
            raise ValueError("Product not found")

        stock = self.stock_service.get_stock_level(
            customer_id, data.product_id, data.source_warehouse_id, data.source_location_id, data.lot_id
        )
        if not stock:
            raise ValueError("No stock at source")

        available = Decimal(str(stock.quantity_on_hand)) - Decimal(str(stock.quantity_reserved))
        if data.quantity > available:
            raise ValueError(f"Insufficient stock. Available: {available}")

        movement = StockMovement(
            customer_id=customer_id,
            movement_number=self._generate_number(customer_id, "TRF"),
            movement_type=MovementTypeEnum.TRANSFER.value,
            movement_date=data.movement_date or datetime.utcnow(),
            product_id=data.product_id,
            lot_id=data.lot_id,
            source_warehouse_id=data.source_warehouse_id,
            source_location_id=data.source_location_id,
            dest_warehouse_id=data.dest_warehouse_id,
            dest_location_id=data.dest_location_id,
            quantity=data.quantity,
            uom_id=product.uom_id,
            unit_cost=stock.unit_cost or Decimal("0"),
            total_cost=data.quantity * (stock.unit_cost or Decimal("0")),
            status=MovementStatusEnum.DRAFT.value,
            reason=data.reason,
            notes=data.notes,
            created_by=created_by,
        )
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(movement)
        return movement

    def create_adjustment(self, customer_id: UUID, data: AdjustmentCreate, created_by: UUID = None) -> StockMovement:
        product = self.db.query(Product).get(data.product_id)
        if not product:
            raise ValueError("Product not found")

        stock = self.stock_service.get_stock_level(
            customer_id, data.product_id, data.warehouse_id, data.location_id, data.lot_id
        )
        unit_cost = stock.unit_cost if stock else product.standard_cost or Decimal("0")

        if data.quantity_change > 0:
            src_wh, src_loc, dst_wh, dst_loc = None, None, data.warehouse_id, data.location_id
        else:
            src_wh, src_loc, dst_wh, dst_loc = data.warehouse_id, data.location_id, None, None

        movement = StockMovement(
            customer_id=customer_id,
            movement_number=self._generate_number(customer_id, "ADJ"),
            movement_type=MovementTypeEnum.ADJUSTMENT.value,
            movement_date=data.movement_date or datetime.utcnow(),
            product_id=data.product_id,
            lot_id=data.lot_id,
            source_warehouse_id=src_wh,
            source_location_id=src_loc,
            dest_warehouse_id=dst_wh,
            dest_location_id=dst_loc,
            quantity=abs(data.quantity_change),
            uom_id=product.uom_id,
            unit_cost=unit_cost,
            total_cost=abs(data.quantity_change) * unit_cost,
            reference_type="inventory_count" if data.count_id else "manual",
            reference_id=data.count_id,
            status=MovementStatusEnum.DRAFT.value,
            reason=data.reason,
            notes=data.notes,
            created_by=created_by,
        )
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(movement)
        return movement

    def confirm_movement(self, movement_id: UUID, confirmed_by: UUID = None) -> StockMovement:
        movement = self.db.query(StockMovement).get(movement_id)
        if not movement or movement.status != MovementStatusEnum.DRAFT.value:
            raise ValueError("Cannot confirm movement")

        if movement.movement_type == MovementTypeEnum.RECEIPT.value:
            self._process_receipt(movement)
        elif movement.movement_type == MovementTypeEnum.ISSUE.value:
            self._process_issue(movement)
        elif movement.movement_type == MovementTypeEnum.TRANSFER.value:
            self._process_transfer(movement)
        elif movement.movement_type == MovementTypeEnum.ADJUSTMENT.value:
            if movement.dest_warehouse_id:
                self._process_receipt(movement)
            else:
                self._process_issue(movement)

        movement.status = MovementStatusEnum.DONE.value
        movement.confirmed_by = confirmed_by
        movement.confirmed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(movement)
        return movement

    def _process_receipt(self, movement: StockMovement):
        stock = self.stock_service.get_or_create_stock_level(
            movement.customer_id, movement.product_id,
            movement.dest_warehouse_id, movement.dest_location_id, movement.lot_id
        )
        stock.quantity_on_hand += movement.quantity
        stock.last_movement_date = datetime.utcnow()
        if movement.unit_cost > 0:
            old_val = stock.quantity_on_hand * (stock.unit_cost or Decimal("0"))
            new_val = movement.quantity * movement.unit_cost
            new_qty = stock.quantity_on_hand + movement.quantity
            stock.unit_cost = (old_val + new_val) / new_qty if new_qty > 0 else movement.unit_cost

        layer = StockValuationLayer(
            customer_id=movement.customer_id, product_id=movement.product_id,
            warehouse_id=movement.dest_warehouse_id, lot_id=movement.lot_id,
            layer_date=movement.movement_date, movement_id=movement.id,
            quantity_initial=movement.quantity, quantity_remaining=movement.quantity,
            unit_cost=movement.unit_cost
        )
        self.db.add(layer)

    def _process_issue(self, movement: StockMovement):
        stock = self.stock_service.get_stock_level(
            movement.customer_id, movement.product_id,
            movement.source_warehouse_id, movement.source_location_id, movement.lot_id
        )
        if stock:
            stock.quantity_on_hand -= movement.quantity
            stock.last_movement_date = datetime.utcnow()

    def _process_transfer(self, movement: StockMovement):
        src = self.stock_service.get_stock_level(
            movement.customer_id, movement.product_id,
            movement.source_warehouse_id, movement.source_location_id, movement.lot_id
        )
        if src:
            src.quantity_on_hand -= movement.quantity
            src.last_movement_date = datetime.utcnow()

        dst = self.stock_service.get_or_create_stock_level(
            movement.customer_id, movement.product_id,
            movement.dest_warehouse_id, movement.dest_location_id, movement.lot_id
        )
        dst.quantity_on_hand += movement.quantity
        dst.unit_cost = movement.unit_cost
        dst.last_movement_date = datetime.utcnow()

    def get_movements(self, customer_id: UUID, filters: MovementFilter = None,
                      page: int = 1, page_size: int = 50) -> Tuple[List[StockMovement], int]:
        query = self.db.query(StockMovement).filter(StockMovement.customer_id == customer_id)

        if filters:
            if filters.product_id:
                query = query.filter(StockMovement.product_id == filters.product_id)
            if filters.warehouse_id:
                query = query.filter(
                    (StockMovement.source_warehouse_id == filters.warehouse_id) |
                    (StockMovement.dest_warehouse_id == filters.warehouse_id)
                )
            if filters.movement_type:
                query = query.filter(StockMovement.movement_type == filters.movement_type.value)
            if filters.status:
                query = query.filter(StockMovement.status == filters.status.value)
            if filters.date_from:
                query = query.filter(StockMovement.movement_date >= filters.date_from)
            if filters.date_to:
                query = query.filter(StockMovement.movement_date <= filters.date_to)

        total = query.count()
        movements = query.options(
            joinedload(StockMovement.product)
        ).order_by(StockMovement.movement_date.desc()).offset((page-1)*page_size).limit(page_size).all()
        return movements, total

    def cancel_movement(self, movement_id: UUID, reason: str) -> StockMovement:
        movement = self.db.query(StockMovement).get(movement_id)
        if not movement or movement.status != MovementStatusEnum.DRAFT.value:
            raise ValueError("Cannot cancel")
        movement.status = MovementStatusEnum.CANCELLED.value
        movement.reason = f"Cancelled: {reason}"
        self.db.commit()
        return movement


def get_movement_service(db: Session) -> MovementService:
    return MovementService(db)
