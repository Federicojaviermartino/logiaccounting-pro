"""
Fulfillment Service
Business logic for pick lists and shipments
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID
import uuid

from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session, selectinload
from fastapi import Depends, HTTPException, status

from app.database import get_db
from app.sales.fulfillment.models import (
    PickList, PickListLine, Shipment, ShipmentLine,
    PickListStatusEnum, PickLineStatusEnum,
    ShipmentStatusEnum
)
from app.sales.fulfillment.schemas import (
    PickListCreate, PickListUpdate, PickListFilter,
    PickLineCreate, PickLineUpdate, PickConfirmRequest,
    GeneratePickListRequest,
    ShipmentCreate, ShipmentUpdate, ShipmentFilter,
    ShipmentLineCreate, ShipConfirmRequest, DeliveryConfirmRequest,
    CreateShipmentFromPickRequest, CreateShipmentFromOrderRequest
)
from app.sales.orders.models import (
    SalesOrder, SalesOrderLine, SOStatusEnum, SOLineStatusEnum
)


class PickListService:
    """Service for pick list operations."""

    def __init__(self, db: Session, customer_id: UUID):
        self.db = db
        self.customer_id = customer_id

    def _generate_pick_number(self) -> str:
        """Generate unique pick number."""
        today = date.today()
        prefix = f"PK-{today.strftime('%Y%m%d')}"

        result = self.db.execute(
            select(func.count(PickList.id)).where(
                and_(
                    PickList.customer_id == self.customer_id,
                    PickList.pick_number.like(f"{prefix}%")
                )
            )
        )
        count = result.scalar() or 0

        return f"{prefix}-{count + 1:04d}"

    def create_pick_list(
        self,
        data: PickListCreate,
        created_by: Optional[UUID] = None
    ) -> PickList:
        """Create new pick list."""
        pick_list = PickList(
            id=uuid.uuid4(),
            customer_id=self.customer_id,
            pick_number=self._generate_pick_number(),
            warehouse_id=data.warehouse_id,
            pick_date=data.pick_date or date.today(),
            due_date=data.due_date,
            assigned_to=data.assigned_to,
            assigned_at=datetime.utcnow() if data.assigned_to else None,
            notes=data.notes,
            status=PickListStatusEnum.DRAFT.value,
            created_by=created_by,
        )

        self.db.add(pick_list)
        self.db.flush()

        if data.lines:
            for idx, line_data in enumerate(data.lines, start=1):
                line = self._create_pick_line(pick_list.id, idx, line_data)
                self.db.add(line)

            self.db.flush()
            self._refresh_with_lines(pick_list)
            pick_list.update_counts()

        self.db.commit()
        self.db.refresh(pick_list)
        return pick_list

    def _create_pick_line(
        self,
        pick_list_id: UUID,
        line_number: int,
        data: PickLineCreate
    ) -> PickListLine:
        """Create pick line."""
        return PickListLine(
            id=uuid.uuid4(),
            pick_list_id=pick_list_id,
            line_number=line_number,
            order_id=data.order_id,
            order_line_id=data.order_line_id,
            allocation_id=data.allocation_id,
            product_id=data.product_id,
            location_id=data.location_id,
            lot_id=data.lot_id,
            quantity_requested=data.quantity_requested,
            notes=data.notes,
            status=PickLineStatusEnum.PENDING.value,
        )

    def update_pick_list(
        self,
        pick_list_id: UUID,
        data: PickListUpdate
    ) -> PickList:
        """Update pick list."""
        pick_list = self.get_pick_list(pick_list_id)
        if not pick_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pick list not found"
            )

        if not pick_list.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit pick list in current status"
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pick_list, field, value)

        if "assigned_to" in update_data and update_data["assigned_to"]:
            pick_list.assigned_at = datetime.utcnow()

        pick_list.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(pick_list)
        return pick_list

    def get_pick_list(
        self,
        pick_list_id: UUID,
        include_lines: bool = True
    ) -> Optional[PickList]:
        """Get pick list by ID."""
        query = select(PickList).where(
            and_(
                PickList.id == pick_list_id,
                PickList.customer_id == self.customer_id
            )
        )

        if include_lines:
            query = query.options(
                selectinload(PickList.lines).selectinload(PickListLine.product),
                selectinload(PickList.lines).selectinload(PickListLine.location),
                selectinload(PickList.lines).selectinload(PickListLine.order),
                selectinload(PickList.warehouse)
            )

        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_pick_lists(
        self,
        filters: PickListFilter,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[PickList], int]:
        """Get pick lists with filters."""
        query = select(PickList).where(
            PickList.customer_id == self.customer_id
        )

        if filters.warehouse_id:
            query = query.where(PickList.warehouse_id == filters.warehouse_id)

        if filters.status:
            query = query.where(PickList.status == filters.status.value)

        if filters.statuses:
            query = query.where(
                PickList.status.in_([s.value for s in filters.statuses])
            )

        if filters.assigned_to:
            query = query.where(PickList.assigned_to == filters.assigned_to)

        if filters.date_from:
            query = query.where(PickList.pick_date >= filters.date_from)

        if filters.date_to:
            query = query.where(PickList.pick_date <= filters.date_to)

        if filters.due_date_from:
            query = query.where(PickList.due_date >= filters.due_date_from)

        if filters.due_date_to:
            query = query.where(PickList.due_date <= filters.due_date_to)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar() or 0

        query = query.options(
            selectinload(PickList.warehouse),
            selectinload(PickList.lines)
        )
        query = query.order_by(PickList.pick_date.desc())
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        pick_lists = result.scalars().all()

        return list(pick_lists), total

    def release_pick_list(
        self,
        pick_list_id: UUID
    ) -> PickList:
        """Release pick list for picking."""
        pick_list = self.get_pick_list(pick_list_id)
        if not pick_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pick list not found"
            )

        if pick_list.status != PickListStatusEnum.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft pick lists can be released"
            )

        if not pick_list.lines:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pick list has no lines"
            )

        pick_list.status = PickListStatusEnum.RELEASED.value
        pick_list.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(pick_list)
        return pick_list

    def start_picking(
        self,
        pick_list_id: UUID,
        user_id: Optional[UUID] = None
    ) -> PickList:
        """Start picking process."""
        pick_list = self.get_pick_list(pick_list_id)
        if not pick_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pick list not found"
            )

        if pick_list.status != PickListStatusEnum.RELEASED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pick list must be released first"
            )

        pick_list.status = PickListStatusEnum.IN_PROGRESS.value
        pick_list.started_at = datetime.utcnow()
        if user_id and not pick_list.assigned_to:
            pick_list.assigned_to = user_id
            pick_list.assigned_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(pick_list)
        return pick_list

    def confirm_picks(
        self,
        pick_list_id: UUID,
        request: PickConfirmRequest,
        picked_by: Optional[UUID] = None
    ) -> PickList:
        """Confirm picked quantities."""
        pick_list = self.get_pick_list(pick_list_id)
        if not pick_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pick list not found"
            )

        if pick_list.status != PickListStatusEnum.IN_PROGRESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pick list must be in progress"
            )

        for confirm_line in request.lines:
            line = next(
                (l for l in pick_list.lines if l.id == confirm_line.line_id),
                None
            )
            if not line:
                continue

            line.quantity_picked = confirm_line.quantity_picked
            if confirm_line.location_id:
                line.location_id = confirm_line.location_id
            if confirm_line.lot_id:
                line.lot_id = confirm_line.lot_id
            if confirm_line.notes:
                line.notes = confirm_line.notes

            line.picked_at = datetime.utcnow()
            line.picked_by = picked_by

            if line.quantity_picked >= line.quantity_requested:
                line.status = PickLineStatusEnum.PICKED.value
            elif line.quantity_picked > 0:
                line.status = PickLineStatusEnum.SHORT.value
            else:
                line.status = PickLineStatusEnum.SHORT.value

        pick_list.update_counts()

        self.db.commit()
        self.db.refresh(pick_list)
        return pick_list

    def complete_pick_list(
        self,
        pick_list_id: UUID
    ) -> PickList:
        """Complete pick list."""
        pick_list = self.get_pick_list(pick_list_id)
        if not pick_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pick list not found"
            )

        if not pick_list.can_complete:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot complete pick list - not all lines are processed"
            )

        pick_list.status = PickListStatusEnum.COMPLETED.value
        pick_list.completed_at = datetime.utcnow()

        for line in pick_list.lines:
            if line.status == PickLineStatusEnum.PICKED.value:
                self._update_order_line_picked(line)

        self.db.commit()
        self.db.refresh(pick_list)
        return pick_list

    def _update_order_line_picked(self, pick_line: PickListLine):
        """Update order line with picked quantity."""
        order_line = self.db.get(SalesOrderLine, pick_line.order_line_id)
        if order_line:
            order_line.qty_picked = (
                (order_line.qty_picked or Decimal("0")) + pick_line.quantity_picked
            )
            if order_line.qty_picked >= order_line.quantity:
                order_line.status = SOLineStatusEnum.PICKING.value

    def cancel_pick_list(
        self,
        pick_list_id: UUID,
        reason: Optional[str] = None
    ) -> PickList:
        """Cancel pick list."""
        pick_list = self.get_pick_list(pick_list_id)
        if not pick_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pick list not found"
            )

        if pick_list.status == PickListStatusEnum.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel completed pick list"
            )

        pick_list.status = PickListStatusEnum.CANCELLED.value
        pick_list.notes = f"{pick_list.notes or ''}\nCancelled: {reason or 'No reason'}".strip()

        for line in pick_list.lines:
            line.status = PickLineStatusEnum.CANCELLED.value

        self.db.commit()
        self.db.refresh(pick_list)
        return pick_list

    def generate_from_orders(
        self,
        request: GeneratePickListRequest,
        created_by: Optional[UUID] = None
    ) -> PickList:
        """Generate pick list from orders."""
        orders = self.db.execute(
            select(SalesOrder).where(
                and_(
                    SalesOrder.id.in_(request.order_ids),
                    SalesOrder.customer_id == self.customer_id,
                    SalesOrder.status.in_([
                        SOStatusEnum.CONFIRMED.value,
                        SOStatusEnum.PROCESSING.value
                    ])
                )
            ).options(selectinload(SalesOrder.lines))
        ).scalars().all()

        if not orders:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid orders found"
            )

        pick_list = PickList(
            id=uuid.uuid4(),
            customer_id=self.customer_id,
            pick_number=self._generate_pick_number(),
            warehouse_id=request.warehouse_id,
            pick_date=date.today(),
            due_date=request.due_date,
            assigned_to=request.assigned_to,
            assigned_at=datetime.utcnow() if request.assigned_to else None,
            status=PickListStatusEnum.DRAFT.value,
            created_by=created_by,
        )

        self.db.add(pick_list)
        self.db.flush()

        line_number = 0
        for order in orders:
            for order_line in order.lines:
                if (
                    order_line.status in [
                        SOLineStatusEnum.PENDING.value,
                        SOLineStatusEnum.ALLOCATED.value
                    ] and
                    order_line.qty_pending > 0
                ):
                    line_number += 1
                    pick_line = PickListLine(
                        id=uuid.uuid4(),
                        pick_list_id=pick_list.id,
                        line_number=line_number,
                        order_id=order.id,
                        order_line_id=order_line.id,
                        product_id=order_line.product_id,
                        warehouse_id=order_line.warehouse_id or request.warehouse_id,
                        quantity_requested=order_line.qty_pending,
                        status=PickLineStatusEnum.PENDING.value,
                    )
                    self.db.add(pick_line)

            order.status = SOStatusEnum.PROCESSING.value

        self.db.flush()
        self._refresh_with_lines(pick_list)
        pick_list.update_counts()

        self.db.commit()
        self.db.refresh(pick_list)
        return pick_list

    def _refresh_with_lines(self, pick_list: PickList):
        """Refresh pick list with lines loaded."""
        self.db.refresh(pick_list)


class ShipmentService:
    """Service for shipment operations."""

    def __init__(self, db: Session, customer_id: UUID):
        self.db = db
        self.customer_id = customer_id

    def _generate_shipment_number(self) -> str:
        """Generate unique shipment number."""
        today = date.today()
        prefix = f"SH-{today.strftime('%Y%m%d')}"

        result = self.db.execute(
            select(func.count(Shipment.id)).where(
                and_(
                    Shipment.customer_id == self.customer_id,
                    Shipment.shipment_number.like(f"{prefix}%")
                )
            )
        )
        count = result.scalar() or 0

        return f"{prefix}-{count + 1:04d}"

    def create_shipment(
        self,
        data: ShipmentCreate,
        created_by: Optional[UUID] = None
    ) -> Shipment:
        """Create new shipment."""
        shipment = Shipment(
            id=uuid.uuid4(),
            customer_id=self.customer_id,
            shipment_number=self._generate_shipment_number(),
            warehouse_id=data.warehouse_id,
            ship_date=data.ship_date,
            expected_delivery=data.expected_delivery,
            carrier=data.carrier,
            service_type=data.service_type,
            tracking_number=data.tracking_number,
            tracking_url=data.tracking_url,
            ship_to_name=data.ship_to_name,
            ship_to_address=data.ship_to_address,
            ship_to_city=data.ship_to_city,
            ship_to_state=data.ship_to_state,
            ship_to_postal=data.ship_to_postal,
            ship_to_country=data.ship_to_country,
            ship_to_phone=data.ship_to_phone,
            weight=data.weight,
            weight_uom=data.weight_uom,
            dimensions=data.dimensions,
            package_count=data.package_count,
            shipping_cost=data.shipping_cost,
            insurance_cost=data.insurance_cost,
            notes=data.notes,
            special_instructions=data.special_instructions,
            status=ShipmentStatusEnum.DRAFT.value,
            created_by=created_by,
        )

        self.db.add(shipment)
        self.db.flush()

        if data.lines:
            for idx, line_data in enumerate(data.lines, start=1):
                line = self._create_shipment_line(shipment.id, idx, line_data)
                self.db.add(line)

        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def _create_shipment_line(
        self,
        shipment_id: UUID,
        line_number: int,
        data: ShipmentLineCreate
    ) -> ShipmentLine:
        """Create shipment line."""
        return ShipmentLine(
            id=uuid.uuid4(),
            shipment_id=shipment_id,
            line_number=line_number,
            order_id=data.order_id,
            order_line_id=data.order_line_id,
            pick_line_id=data.pick_line_id,
            product_id=data.product_id,
            lot_id=data.lot_id,
            serial_numbers=data.serial_numbers,
            quantity_shipped=data.quantity_shipped,
        )

    def update_shipment(
        self,
        shipment_id: UUID,
        data: ShipmentUpdate
    ) -> Shipment:
        """Update shipment."""
        shipment = self.get_shipment(shipment_id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipment not found"
            )

        if not shipment.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit shipment in current status"
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(shipment, field, value)

        shipment.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def get_shipment(
        self,
        shipment_id: UUID,
        include_lines: bool = True
    ) -> Optional[Shipment]:
        """Get shipment by ID."""
        query = select(Shipment).where(
            and_(
                Shipment.id == shipment_id,
                Shipment.customer_id == self.customer_id
            )
        )

        if include_lines:
            query = query.options(
                selectinload(Shipment.lines).selectinload(ShipmentLine.product),
                selectinload(Shipment.lines).selectinload(ShipmentLine.order),
                selectinload(Shipment.warehouse)
            )

        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_shipments(
        self,
        filters: ShipmentFilter,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Shipment], int]:
        """Get shipments with filters."""
        query = select(Shipment).where(
            Shipment.customer_id == self.customer_id
        )

        if filters.warehouse_id:
            query = query.where(Shipment.warehouse_id == filters.warehouse_id)

        if filters.status:
            query = query.where(Shipment.status == filters.status.value)

        if filters.statuses:
            query = query.where(
                Shipment.status.in_([s.value for s in filters.statuses])
            )

        if filters.carrier:
            query = query.where(Shipment.carrier.ilike(f"%{filters.carrier}%"))

        if filters.tracking_number:
            query = query.where(
                Shipment.tracking_number.ilike(f"%{filters.tracking_number}%")
            )

        if filters.date_from:
            query = query.where(Shipment.ship_date >= filters.date_from)

        if filters.date_to:
            query = query.where(Shipment.ship_date <= filters.date_to)

        if filters.order_id:
            query = query.join(Shipment.lines).where(
                ShipmentLine.order_id == filters.order_id
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar() or 0

        query = query.options(
            selectinload(Shipment.warehouse),
            selectinload(Shipment.lines)
        )
        query = query.order_by(Shipment.created_at.desc())
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        shipments = result.scalars().all()

        return list(shipments), total

    def pack_shipment(
        self,
        shipment_id: UUID
    ) -> Shipment:
        """Mark shipment as packed."""
        shipment = self.get_shipment(shipment_id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipment not found"
            )

        if shipment.status != ShipmentStatusEnum.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft shipments can be packed"
            )

        if not shipment.lines:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shipment has no lines"
            )

        shipment.status = ShipmentStatusEnum.PACKED.value
        shipment.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def ship(
        self,
        shipment_id: UUID,
        request: ShipConfirmRequest,
        shipped_by: Optional[UUID] = None
    ) -> Shipment:
        """Confirm shipment shipped."""
        shipment = self.get_shipment(shipment_id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipment not found"
            )

        if not shipment.can_ship:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shipment cannot be shipped"
            )

        shipment.status = ShipmentStatusEnum.SHIPPED.value
        shipment.ship_date = request.ship_date or date.today()
        shipment.shipped_at = datetime.utcnow()
        shipment.shipped_by = shipped_by

        if request.tracking_number:
            shipment.tracking_number = request.tracking_number
        if request.tracking_url:
            shipment.tracking_url = request.tracking_url
        if request.carrier:
            shipment.carrier = request.carrier

        for line in shipment.lines:
            self._update_order_line_shipped(line)

        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def _update_order_line_shipped(self, ship_line: ShipmentLine):
        """Update order line with shipped quantity."""
        order_line = self.db.get(SalesOrderLine, ship_line.order_line_id)
        if order_line:
            order_line.qty_shipped = (
                (order_line.qty_shipped or Decimal("0")) + ship_line.quantity_shipped
            )
            if order_line.qty_shipped >= order_line.quantity:
                order_line.status = SOLineStatusEnum.SHIPPED.value
            else:
                order_line.status = SOLineStatusEnum.PARTIAL_SHIPPED.value

        order = self.db.get(SalesOrder, ship_line.order_id)
        if order:
            order.qty_shipped = sum(
                l.qty_shipped or Decimal("0") for l in order.lines
            )
            if order.fully_shipped:
                order.status = SOStatusEnum.SHIPPED.value
            else:
                order.status = SOStatusEnum.PARTIAL_SHIPPED.value

    def confirm_delivery(
        self,
        shipment_id: UUID,
        request: DeliveryConfirmRequest
    ) -> Shipment:
        """Confirm shipment delivered."""
        shipment = self.get_shipment(shipment_id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipment not found"
            )

        if shipment.status not in [
            ShipmentStatusEnum.SHIPPED.value,
            ShipmentStatusEnum.IN_TRANSIT.value
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shipment must be shipped first"
            )

        shipment.status = ShipmentStatusEnum.DELIVERED.value
        shipment.actual_delivery = request.delivery_date
        if request.notes:
            shipment.notes = f"{shipment.notes or ''}\nDelivery: {request.notes}".strip()

        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def cancel_shipment(
        self,
        shipment_id: UUID,
        reason: Optional[str] = None
    ) -> Shipment:
        """Cancel shipment."""
        shipment = self.get_shipment(shipment_id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipment not found"
            )

        if shipment.status in [
            ShipmentStatusEnum.SHIPPED.value,
            ShipmentStatusEnum.DELIVERED.value
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel shipped/delivered shipment"
            )

        shipment.status = ShipmentStatusEnum.CANCELLED.value
        shipment.notes = f"{shipment.notes or ''}\nCancelled: {reason or 'No reason'}".strip()

        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def create_from_pick_list(
        self,
        request: CreateShipmentFromPickRequest,
        created_by: Optional[UUID] = None
    ) -> Shipment:
        """Create shipment from completed pick list."""
        pick_list = self.db.execute(
            select(PickList).where(
                and_(
                    PickList.id == request.pick_list_id,
                    PickList.customer_id == self.customer_id,
                    PickList.status == PickListStatusEnum.COMPLETED.value
                )
            ).options(selectinload(PickList.lines))
        ).scalar_one_or_none()

        if not pick_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed pick list not found"
            )

        shipment = Shipment(
            id=uuid.uuid4(),
            customer_id=self.customer_id,
            shipment_number=self._generate_shipment_number(),
            warehouse_id=pick_list.warehouse_id,
            ship_to_name=request.ship_to_name,
            ship_to_address=request.ship_to_address,
            carrier=request.carrier,
            service_type=request.service_type,
            status=ShipmentStatusEnum.DRAFT.value,
            created_by=created_by,
        )

        self.db.add(shipment)
        self.db.flush()

        line_number = 0
        for pick_line in pick_list.lines:
            if (
                pick_line.status == PickLineStatusEnum.PICKED.value and
                pick_line.quantity_picked > 0
            ):
                line_number += 1
                ship_line = ShipmentLine(
                    id=uuid.uuid4(),
                    shipment_id=shipment.id,
                    line_number=line_number,
                    order_id=pick_line.order_id,
                    order_line_id=pick_line.order_line_id,
                    pick_line_id=pick_line.id,
                    product_id=pick_line.product_id,
                    lot_id=pick_line.lot_id,
                    quantity_shipped=pick_line.quantity_picked,
                )
                self.db.add(ship_line)

        self.db.commit()
        self.db.refresh(shipment)
        return shipment


def get_pick_list_service(
    db: Session = Depends(get_db),
    customer_id: UUID = None
) -> PickListService:
    """Get pick list service instance."""
    return PickListService(db, customer_id)


def get_shipment_service(
    db: Session = Depends(get_db),
    customer_id: UUID = None
) -> ShipmentService:
    """Get shipment service instance."""
    return ShipmentService(db, customer_id)
