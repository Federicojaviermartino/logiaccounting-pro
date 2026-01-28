"""
Sales Order Service
Business logic for sales orders
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID
import uuid

from sqlalchemy import select, func, and_, or_

from app.utils.datetime_utils import utc_now
from sqlalchemy.orm import Session, selectinload
from fastapi import Depends, HTTPException, status

from app.database import get_db
from app.sales.orders.models import (
    SalesOrder, SalesOrderLine, StockAllocation,
    SOStatusEnum, SOLineStatusEnum, PriorityEnum
)
from app.sales.orders.schemas import (
    SalesOrderCreate, SalesOrderUpdate, SalesOrderFilter,
    OrderLineCreate, OrderLineUpdate,
    AllocationCreate, OrderConfirmRequest, OrderHoldRequest,
    BulkLineUpdate, OrderDuplicateRequest
)


class SalesOrderService:
    """Service for sales order operations."""

    def __init__(self, db: Session, customer_id: UUID):
        self.db = db
        self.customer_id = customer_id

    def _generate_order_number(self) -> str:
        """Generate unique order number."""
        today = date.today()
        prefix = f"SO-{today.strftime('%Y%m')}"

        result = self.db.execute(
            select(func.count(SalesOrder.id)).where(
                and_(
                    SalesOrder.customer_id == self.customer_id,
                    SalesOrder.order_number.like(f"{prefix}%")
                )
            )
        )
        count = result.scalar() or 0

        return f"{prefix}-{count + 1:04d}"

    def create_order(
        self,
        data: SalesOrderCreate,
        created_by: Optional[UUID] = None
    ) -> SalesOrder:
        """Create new sales order."""
        order = SalesOrder(
            id=uuid.uuid4(),
            customer_id=self.customer_id,
            order_number=self._generate_order_number(),
            customer_master_id=data.customer_master_id,
            customer_po_number=data.customer_po_number,
            order_date=data.order_date or date.today(),
            requested_date=data.requested_date,
            promised_date=data.promised_date,
            ship_to_address_id=data.ship_to_address_id,
            shipping_address=data.shipping_address,
            shipping_method=data.shipping_method,
            shipping_carrier=data.shipping_carrier,
            warehouse_id=data.warehouse_id,
            payment_term_id=data.payment_term_id,
            currency=data.currency,
            exchange_rate=data.exchange_rate,
            discount_percent=data.discount_percent,
            shipping_amount=data.shipping_amount,
            priority=data.priority.value,
            notes=data.notes,
            internal_notes=data.internal_notes,
            status=SOStatusEnum.DRAFT.value,
            created_by=created_by,
        )

        self.db.add(order)
        self.db.flush()

        if data.lines:
            for idx, line_data in enumerate(data.lines, start=1):
                line = self._create_line(order.id, idx, line_data)
                self.db.add(line)

            self.db.flush()
            self._refresh_order_with_lines(order)
            order.recalculate_totals()

        self.db.commit()
        self.db.refresh(order)
        return order

    def _create_line(
        self,
        order_id: UUID,
        line_number: int,
        data: OrderLineCreate
    ) -> SalesOrderLine:
        """Create order line."""
        line = SalesOrderLine(
            id=uuid.uuid4(),
            order_id=order_id,
            line_number=line_number,
            product_id=data.product_id,
            description=data.description,
            quantity=data.quantity,
            uom_id=data.uom_id,
            unit_price=data.unit_price,
            discount_percent=data.discount_percent,
            tax_rate=data.tax_rate,
            requested_date=data.requested_date,
            promised_date=data.promised_date,
            warehouse_id=data.warehouse_id,
            notes=data.notes,
            status=SOLineStatusEnum.PENDING.value,
        )
        line.calculate_amounts()
        return line

    def update_order(
        self,
        order_id: UUID,
        data: SalesOrderUpdate
    ) -> SalesOrder:
        """Update sales order."""
        order = self.get_order(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if not order.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot edit order in {order.status} status"
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "priority" and value:
                value = value.value
            setattr(order, field, value)

        order.updated_at = utc_now()
        order.recalculate_totals()

        self.db.commit()
        self.db.refresh(order)
        return order

    def get_order(
        self,
        order_id: UUID,
        include_lines: bool = True
    ) -> Optional[SalesOrder]:
        """Get order by ID."""
        query = select(SalesOrder).where(
            and_(
                SalesOrder.id == order_id,
                SalesOrder.customer_id == self.customer_id
            )
        )

        if include_lines:
            query = query.options(
                selectinload(SalesOrder.lines),
                selectinload(SalesOrder.customer_master),
                selectinload(SalesOrder.warehouse),
                selectinload(SalesOrder.allocations)
            )

        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_orders(
        self,
        filters: SalesOrderFilter,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[SalesOrder], int]:
        """Get orders with filters."""
        query = select(SalesOrder).where(
            SalesOrder.customer_id == self.customer_id
        )

        if filters.search:
            search = f"%{filters.search}%"
            query = query.join(SalesOrder.customer_master).where(
                or_(
                    SalesOrder.order_number.ilike(search),
                    SalesOrder.customer_po_number.ilike(search),
                )
            )

        if filters.customer_master_id:
            query = query.where(
                SalesOrder.customer_master_id == filters.customer_master_id
            )

        if filters.status:
            query = query.where(SalesOrder.status == filters.status.value)

        if filters.statuses:
            query = query.where(
                SalesOrder.status.in_([s.value for s in filters.statuses])
            )

        if filters.priority:
            query = query.where(SalesOrder.priority == filters.priority.value)

        if filters.warehouse_id:
            query = query.where(SalesOrder.warehouse_id == filters.warehouse_id)

        if filters.date_from:
            query = query.where(SalesOrder.order_date >= filters.date_from)

        if filters.date_to:
            query = query.where(SalesOrder.order_date <= filters.date_to)

        if filters.requested_date_from:
            query = query.where(
                SalesOrder.requested_date >= filters.requested_date_from
            )

        if filters.requested_date_to:
            query = query.where(
                SalesOrder.requested_date <= filters.requested_date_to
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar() or 0

        query = query.options(
            selectinload(SalesOrder.customer_master),
            selectinload(SalesOrder.warehouse),
            selectinload(SalesOrder.lines)
        )
        query = query.order_by(SalesOrder.order_date.desc())
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        orders = result.scalars().all()

        return list(orders), total

    def add_line(
        self,
        order_id: UUID,
        data: OrderLineCreate
    ) -> SalesOrderLine:
        """Add line to order."""
        order = self.get_order(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if not order.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add lines to this order"
            )

        max_line = max(
            [l.line_number for l in order.lines],
            default=0
        )

        line = self._create_line(order_id, max_line + 1, data)
        self.db.add(line)
        self.db.flush()

        self._refresh_order_with_lines(order)
        order.recalculate_totals()

        self.db.commit()
        self.db.refresh(line)
        return line

    def update_line(
        self,
        order_id: UUID,
        line_id: UUID,
        data: OrderLineUpdate
    ) -> SalesOrderLine:
        """Update order line."""
        order = self.get_order(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if not order.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit lines on this order"
            )

        line = next((l for l in order.lines if l.id == line_id), None)
        if not line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Line not found"
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(line, field, value)

        line.calculate_amounts()
        order.recalculate_totals()

        self.db.commit()
        self.db.refresh(line)
        return line

    def delete_line(self, order_id: UUID, line_id: UUID) -> bool:
        """Delete order line."""
        order = self.get_order(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if not order.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete lines from this order"
            )

        line = next((l for l in order.lines if l.id == line_id), None)
        if not line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Line not found"
            )

        self.db.delete(line)
        self.db.flush()

        self._refresh_order_with_lines(order)
        order.recalculate_totals()

        self.db.commit()
        return True

    def confirm_order(
        self,
        order_id: UUID,
        request: OrderConfirmRequest,
        confirmed_by: Optional[UUID] = None
    ) -> SalesOrder:
        """Confirm order."""
        order = self.get_order(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if not order.can_confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order cannot be confirmed"
            )

        order.status = SOStatusEnum.CONFIRMED.value
        order.confirmed_by = confirmed_by
        order.confirmed_at = utc_now()

        if request.auto_allocate:
            self._auto_allocate_order(order)

        self.db.commit()
        self.db.refresh(order)
        return order

    def _auto_allocate_order(self, order: SalesOrder):
        """Auto-allocate stock for order lines."""
        for line in order.lines:
            if line.status == SOLineStatusEnum.PENDING.value:
                line.status = SOLineStatusEnum.ALLOCATED.value

        order.status = SOStatusEnum.PROCESSING.value

    def set_hold(
        self,
        order_id: UUID,
        request: OrderHoldRequest,
        user_id: Optional[UUID] = None
    ) -> SalesOrder:
        """Set or release hold on order."""
        order = self.get_order(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if request.hold:
            order.status = SOStatusEnum.ON_HOLD.value
            order.hold_reason = request.reason
            order.hold_by = user_id
            order.hold_at = utc_now()
        else:
            if order.status != SOStatusEnum.ON_HOLD.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order is not on hold"
                )
            order.status = SOStatusEnum.DRAFT.value
            order.hold_reason = None
            order.hold_by = None
            order.hold_at = None

        self.db.commit()
        self.db.refresh(order)
        return order

    def cancel_order(
        self,
        order_id: UUID,
        reason: Optional[str] = None
    ) -> SalesOrder:
        """Cancel order."""
        order = self.get_order(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if order.status in [
            SOStatusEnum.SHIPPED.value,
            SOStatusEnum.INVOICED.value,
            SOStatusEnum.CLOSED.value
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel shipped/invoiced order"
            )

        self._release_allocations(order)

        order.status = SOStatusEnum.CANCELLED.value
        order.internal_notes = (
            f"{order.internal_notes or ''}\nCancelled: {reason or 'No reason provided'}"
        ).strip()

        for line in order.lines:
            line.status = SOLineStatusEnum.CANCELLED.value

        self.db.commit()
        self.db.refresh(order)
        return order

    def _release_allocations(self, order: SalesOrder):
        """Release all allocations for order."""
        for allocation in order.allocations:
            self.db.delete(allocation)

        for line in order.lines:
            line.qty_allocated = Decimal("0")
            line.qty_picked = Decimal("0")

        order.qty_allocated = Decimal("0")
        order.qty_picked = Decimal("0")

    def allocate_stock(
        self,
        order_id: UUID,
        data: AllocationCreate,
        allocated_by: Optional[UUID] = None
    ) -> StockAllocation:
        """Allocate stock for order line."""
        order = self.get_order(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        line = next(
            (l for l in order.lines if l.id == data.order_line_id),
            None
        )
        if not line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Line not found"
            )

        if data.quantity > line.qty_to_allocate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Allocation quantity exceeds remaining quantity"
            )

        allocation = StockAllocation(
            id=uuid.uuid4(),
            customer_id=self.customer_id,
            order_id=order_id,
            order_line_id=data.order_line_id,
            product_id=line.product_id,
            warehouse_id=data.warehouse_id,
            location_id=data.location_id,
            lot_id=data.lot_id,
            quantity_allocated=data.quantity,
            allocated_by=allocated_by,
        )

        self.db.add(allocation)

        line.qty_allocated = (line.qty_allocated or Decimal("0")) + data.quantity
        if line.qty_allocated >= line.quantity:
            line.status = SOLineStatusEnum.ALLOCATED.value

        order.qty_allocated = sum(
            l.qty_allocated or Decimal("0") for l in order.lines
        )

        self.db.commit()
        self.db.refresh(allocation)
        return allocation

    def get_allocations(self, order_id: UUID) -> List[StockAllocation]:
        """Get all allocations for order."""
        query = select(StockAllocation).where(
            and_(
                StockAllocation.order_id == order_id,
                StockAllocation.customer_id == self.customer_id
            )
        ).options(
            selectinload(StockAllocation.product),
            selectinload(StockAllocation.location),
            selectinload(StockAllocation.lot)
        )

        result = self.db.execute(query)
        return list(result.scalars().all())

    def deallocate_stock(
        self,
        order_id: UUID,
        allocation_id: UUID
    ) -> bool:
        """Remove stock allocation."""
        allocation = self.db.execute(
            select(StockAllocation).where(
                and_(
                    StockAllocation.id == allocation_id,
                    StockAllocation.order_id == order_id,
                    StockAllocation.customer_id == self.customer_id
                )
            )
        ).scalar_one_or_none()

        if not allocation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Allocation not found"
            )

        order = self.get_order(order_id)
        line = next(
            (l for l in order.lines if l.id == allocation.order_line_id),
            None
        )

        if line:
            line.qty_allocated = (
                (line.qty_allocated or Decimal("0")) - allocation.quantity_allocated
            )
            if line.qty_allocated < line.quantity:
                line.status = SOLineStatusEnum.PENDING.value

        self.db.delete(allocation)

        order.qty_allocated = sum(
            l.qty_allocated or Decimal("0") for l in order.lines
        )

        self.db.commit()
        return True

    def duplicate_order(
        self,
        order_id: UUID,
        request: OrderDuplicateRequest,
        created_by: Optional[UUID] = None
    ) -> SalesOrder:
        """Duplicate an existing order."""
        source = self.get_order(order_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        new_order = SalesOrder(
            id=uuid.uuid4(),
            customer_id=self.customer_id,
            order_number=self._generate_order_number(),
            customer_master_id=request.new_customer_id or source.customer_master_id,
            customer_po_number=None,
            order_date=date.today(),
            requested_date=source.requested_date if request.copy_dates else None,
            promised_date=source.promised_date if request.copy_dates else None,
            ship_to_address_id=source.ship_to_address_id,
            shipping_address=source.shipping_address,
            shipping_method=source.shipping_method,
            shipping_carrier=source.shipping_carrier,
            warehouse_id=source.warehouse_id,
            payment_term_id=source.payment_term_id,
            currency=source.currency,
            exchange_rate=source.exchange_rate,
            discount_percent=source.discount_percent,
            shipping_amount=source.shipping_amount,
            priority=source.priority,
            notes=source.notes,
            internal_notes=f"Duplicated from {source.order_number}",
            status=SOStatusEnum.DRAFT.value,
            created_by=created_by,
        )

        self.db.add(new_order)
        self.db.flush()

        for idx, source_line in enumerate(source.lines, start=1):
            if source_line.status != SOLineStatusEnum.CANCELLED.value:
                line = SalesOrderLine(
                    id=uuid.uuid4(),
                    order_id=new_order.id,
                    line_number=idx,
                    product_id=source_line.product_id,
                    description=source_line.description,
                    quantity=source_line.quantity,
                    uom_id=source_line.uom_id,
                    unit_price=source_line.unit_price if request.copy_prices else Decimal("0"),
                    discount_percent=source_line.discount_percent if request.copy_prices else Decimal("0"),
                    tax_rate=source_line.tax_rate,
                    requested_date=source_line.requested_date if request.copy_dates else None,
                    promised_date=source_line.promised_date if request.copy_dates else None,
                    warehouse_id=source_line.warehouse_id,
                    notes=source_line.notes,
                    status=SOLineStatusEnum.PENDING.value,
                )
                line.calculate_amounts()
                self.db.add(line)

        self.db.flush()
        self._refresh_order_with_lines(new_order)
        new_order.recalculate_totals()

        self.db.commit()
        self.db.refresh(new_order)
        return new_order

    def bulk_update_lines(
        self,
        order_id: UUID,
        data: BulkLineUpdate
    ) -> List[SalesOrderLine]:
        """Bulk update order lines."""
        order = self.get_order(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if not order.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit lines on this order"
            )

        updated_lines = []
        for line in order.lines:
            if line.id in data.line_ids:
                if data.warehouse_id is not None:
                    line.warehouse_id = data.warehouse_id
                if data.requested_date is not None:
                    line.requested_date = data.requested_date
                if data.promised_date is not None:
                    line.promised_date = data.promised_date
                updated_lines.append(line)

        self.db.commit()
        return updated_lines

    def _refresh_order_with_lines(self, order: SalesOrder):
        """Refresh order with lines loaded."""
        self.db.refresh(order)
        for line in order.lines:
            self.db.refresh(line)

    def get_order_stats(self) -> dict:
        """Get order statistics."""
        result = self.db.execute(
            select(
                SalesOrder.status,
                func.count(SalesOrder.id).label("count"),
                func.sum(SalesOrder.total_amount).label("total")
            ).where(
                SalesOrder.customer_id == self.customer_id
            ).group_by(SalesOrder.status)
        )

        stats = {
            "by_status": {},
            "total_orders": 0,
            "total_amount": Decimal("0")
        }

        for row in result:
            stats["by_status"][row.status] = {
                "count": row.count,
                "total": float(row.total or 0)
            }
            stats["total_orders"] += row.count
            stats["total_amount"] += row.total or Decimal("0")

        stats["total_amount"] = float(stats["total_amount"])
        return stats


def get_order_service(
    db: Session = Depends(get_db),
    customer_id: UUID = None
) -> SalesOrderService:
    """Get sales order service instance."""
    return SalesOrderService(db, customer_id)
