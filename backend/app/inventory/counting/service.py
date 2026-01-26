"""Inventory Counting Service"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.inventory.counting.models import InventoryCount, InventoryCountLine, CountTypeEnum, CountStatusEnum
from app.inventory.stock.models import StockLevel
from app.inventory.movements.service import MovementService
from app.inventory.movements.schemas import AdjustmentCreate


class CountingService:
    def __init__(self, db: Session):
        self.db = db
        self.movement_service = MovementService(db)

    def _generate_number(self, customer_id: UUID) -> str:
        date_str = datetime.utcnow().strftime("%Y%m")
        last = self.db.query(InventoryCount).filter(
            InventoryCount.customer_id == customer_id,
            InventoryCount.count_number.like(f"CNT-{date_str}-%")
        ).order_by(InventoryCount.count_number.desc()).first()
        seq = int(last.count_number.split("-")[-1]) + 1 if last else 1
        return f"CNT-{date_str}-{seq:05d}"

    def create_count(
        self,
        customer_id: UUID,
        warehouse_id: UUID,
        count_type: str,
        include_all: bool = False,
        category_ids: List[UUID] = None,
        location_ids: List[UUID] = None,
        scheduled_date: datetime = None,
        created_by: UUID = None,
    ) -> InventoryCount:
        count = InventoryCount(
            customer_id=customer_id,
            count_number=self._generate_number(customer_id),
            count_type=count_type,
            warehouse_id=warehouse_id,
            include_all_products=include_all,
            category_ids=category_ids,
            location_ids=location_ids,
            scheduled_date=scheduled_date,
            created_by=created_by,
        )
        self.db.add(count)
        self.db.commit()
        self.db.refresh(count)
        return count

    def generate_count_lines(self, count_id: UUID) -> int:
        """Generate lines from current stock levels."""
        count = self.db.query(InventoryCount).get(count_id)
        if not count or count.status != CountStatusEnum.DRAFT.value:
            raise ValueError("Invalid count")

        # Query stock levels
        query = self.db.query(StockLevel).filter(
            StockLevel.customer_id == count.customer_id,
            StockLevel.warehouse_id == count.warehouse_id,
        )

        if count.location_ids:
            query = query.filter(StockLevel.location_id.in_(count.location_ids))

        if not count.include_all_products:
            query = query.filter(StockLevel.quantity_on_hand > 0)

        stocks = query.all()

        for stock in stocks:
            line = InventoryCountLine(
                count_id=count_id,
                product_id=stock.product_id,
                location_id=stock.location_id,
                lot_id=stock.lot_id,
                system_quantity=stock.quantity_on_hand,
                system_unit_cost=stock.unit_cost,
            )
            self.db.add(line)

        count.total_lines = len(stocks)
        self.db.commit()

        return len(stocks)

    def start_count(self, count_id: UUID) -> InventoryCount:
        count = self.db.query(InventoryCount).get(count_id)
        if not count or count.status != CountStatusEnum.DRAFT.value:
            raise ValueError("Cannot start count")

        if count.total_lines == 0:
            self.generate_count_lines(count_id)

        count.status = CountStatusEnum.IN_PROGRESS.value
        count.started_at = datetime.utcnow()
        self.db.commit()
        return count

    def record_count(
        self,
        line_id: UUID,
        counted_quantity: Decimal,
        counted_by: UUID = None,
        notes: str = None,
    ) -> InventoryCountLine:
        line = self.db.query(InventoryCountLine).get(line_id)
        if not line:
            raise ValueError("Line not found")

        line.counted_quantity = counted_quantity
        line.counted_by = counted_by
        line.counted_at = datetime.utcnow()
        line.status = "counted"
        line.notes = notes

        # Calculate variance
        variance = counted_quantity - line.system_quantity
        line.variance_value = variance * (line.system_unit_cost or Decimal("0"))

        # Update count progress
        count = line.count
        count.lines_counted = self.db.query(InventoryCountLine).filter(
            InventoryCountLine.count_id == count.id,
            InventoryCountLine.status != "pending"
        ).count()

        count.lines_with_variance = self.db.query(InventoryCountLine).filter(
            InventoryCountLine.count_id == count.id,
            InventoryCountLine.variance_quantity != 0
        ).count()

        self.db.commit()
        self.db.refresh(line)
        return line

    def complete_count(self, count_id: UUID) -> InventoryCount:
        count = self.db.query(InventoryCount).get(count_id)
        if not count or count.status != CountStatusEnum.IN_PROGRESS.value:
            raise ValueError("Cannot complete")

        # Check all lines counted
        pending = self.db.query(InventoryCountLine).filter(
            InventoryCountLine.count_id == count_id,
            InventoryCountLine.status == "pending"
        ).count()

        if pending > 0:
            raise ValueError(f"{pending} lines still pending")

        # Calculate total variance
        total_var = self.db.query(func.sum(InventoryCountLine.variance_value)).filter(
            InventoryCountLine.count_id == count_id
        ).scalar() or Decimal("0")

        count.total_variance_value = total_var
        count.status = CountStatusEnum.PENDING_REVIEW.value
        count.completed_at = datetime.utcnow()
        self.db.commit()
        return count

    def approve_and_post(
        self,
        count_id: UUID,
        approved_by: UUID = None,
    ) -> InventoryCount:
        """Approve count and create adjustment movements."""
        count = self.db.query(InventoryCount).get(count_id)
        if not count or count.status != CountStatusEnum.PENDING_REVIEW.value:
            raise ValueError("Cannot approve")

        # Get lines with variance
        lines = self.db.query(InventoryCountLine).filter(
            InventoryCountLine.count_id == count_id,
            InventoryCountLine.variance_quantity != 0
        ).all()

        # Create adjustments
        for line in lines:
            adj = AdjustmentCreate(
                product_id=line.product_id,
                warehouse_id=count.warehouse_id,
                location_id=line.location_id,
                quantity_change=line.variance_quantity,
                lot_id=line.lot_id,
                reason=f"Inventory count {count.count_number}",
                count_id=count_id,
            )
            movement = self.movement_service.create_adjustment(
                count.customer_id, adj, approved_by
            )
            self.movement_service.confirm_movement(movement.id, approved_by)

        count.status = CountStatusEnum.POSTED.value
        count.approved_by = approved_by
        count.approved_at = datetime.utcnow()
        self.db.commit()
        return count

    def get_counts(
        self,
        customer_id: UUID,
        warehouse_id: UUID = None,
        status: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[InventoryCount], int]:
        query = self.db.query(InventoryCount).filter(
            InventoryCount.customer_id == customer_id
        )

        if warehouse_id:
            query = query.filter(InventoryCount.warehouse_id == warehouse_id)
        if status:
            query = query.filter(InventoryCount.status == status)

        total = query.count()
        counts = query.options(
            joinedload(InventoryCount.warehouse)
        ).order_by(InventoryCount.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()

        return counts, total

    def get_count_lines(self, count_id: UUID) -> List[InventoryCountLine]:
        return self.db.query(InventoryCountLine).filter(
            InventoryCountLine.count_id == count_id
        ).options(
            joinedload(InventoryCountLine.product),
            joinedload(InventoryCountLine.location),
        ).all()


def get_counting_service(db: Session) -> CountingService:
    return CountingService(db)
