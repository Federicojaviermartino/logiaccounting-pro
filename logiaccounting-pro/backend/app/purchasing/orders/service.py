"""
Purchase Order Service
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy import func, or_, and_, extract
from sqlalchemy.orm import Session, joinedload

from app.purchasing.orders.models import (
    PurchaseOrder, PurchaseOrderLine, PurchaseOrderApproval,
    POStatusEnum, POLineStatusEnum
)
from app.purchasing.orders.schemas import (
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderFilter,
    OrderLineCreate, OrderLineUpdate, AddLineRequest,
)
from app.purchasing.suppliers.models import Supplier, SupplierPriceList
from app.inventory.products.models import Product

logger = logging.getLogger(__name__)


class PurchaseOrderService:
    """Service for purchase orders."""

    def __init__(self, db: Session):
        self.db = db

    def _generate_order_number(self, customer_id: UUID) -> str:
        """Generate unique PO number."""
        year = datetime.utcnow().strftime("%y")

        last = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.customer_id == customer_id,
            PurchaseOrder.order_number.like(f"PO-{year}%")
        ).order_by(PurchaseOrder.order_number.desc()).first()

        if last:
            try:
                last_num = int(last.order_number.split("-")[-1])
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1

        return f"PO-{year}-{next_num:06d}"

    def _get_product_price(
        self,
        supplier_id: UUID,
        product_id: UUID,
        quantity: Decimal,
    ) -> Optional[Decimal]:
        """Get price from supplier price list."""
        today = date.today()

        price = self.db.query(SupplierPriceList).filter(
            SupplierPriceList.supplier_id == supplier_id,
            SupplierPriceList.product_id == product_id,
            SupplierPriceList.min_quantity <= quantity,
            or_(
                SupplierPriceList.valid_from == None,
                SupplierPriceList.valid_from <= today,
            ),
            or_(
                SupplierPriceList.valid_to == None,
                SupplierPriceList.valid_to >= today,
            ),
        ).order_by(
            SupplierPriceList.min_quantity.desc()  # Get highest tier applicable
        ).first()

        return price.unit_price if price else None

    def create_order(
        self,
        customer_id: UUID,
        data: PurchaseOrderCreate,
        created_by: UUID = None,
    ) -> PurchaseOrder:
        """Create purchase order."""
        # Validate supplier
        supplier = self.db.query(Supplier).get(data.supplier_id)
        if not supplier or supplier.customer_id != customer_id:
            raise ValueError("Supplier not found")

        if not supplier.is_active:
            raise ValueError("Supplier is not active")

        # Create order
        order = PurchaseOrder(
            customer_id=customer_id,
            order_number=self._generate_order_number(customer_id),
            supplier_id=data.supplier_id,
            order_date=data.order_date or date.today(),
            expected_date=data.expected_date,
            delivery_warehouse_id=data.delivery_warehouse_id or supplier.default_warehouse_id,
            delivery_address=data.delivery_address,
            payment_term_id=data.payment_term_id or supplier.payment_term_id,
            currency=data.currency or supplier.currency,
            exchange_rate=data.exchange_rate,
            discount_amount=data.discount_amount,
            shipping_amount=data.shipping_amount,
            supplier_contact_id=data.supplier_contact_id,
            reference=data.reference,
            requisition_id=data.requisition_id,
            notes=data.notes,
            internal_notes=data.internal_notes,
            created_by=created_by,
        )

        self.db.add(order)
        self.db.flush()

        # Add lines
        for idx, line_data in enumerate(data.lines, start=1):
            product = self.db.query(Product).get(line_data.product_id)
            if not product:
                raise ValueError(f"Product not found: {line_data.product_id}")

            # Get price from supplier list if not provided
            unit_price = line_data.unit_price
            if unit_price is None or unit_price == 0:
                unit_price = self._get_product_price(
                    data.supplier_id, line_data.product_id, line_data.quantity
                )
            if unit_price is None:
                unit_price = product.standard_cost or Decimal("0")

            line = PurchaseOrderLine(
                order_id=order.id,
                line_number=idx,
                product_id=line_data.product_id,
                description=line_data.description or product.name,
                supplier_sku=line_data.supplier_sku,
                quantity=line_data.quantity,
                uom_id=product.uom_id,
                unit_price=unit_price,
                discount_percent=line_data.discount_percent,
                tax_rate=line_data.tax_rate,
                expected_date=line_data.expected_date or data.expected_date,
                warehouse_id=line_data.warehouse_id or order.delivery_warehouse_id,
                notes=line_data.notes,
            )
            line.calculate_amounts()
            self.db.add(line)

        self.db.flush()
        order.recalculate_totals()

        # Check if approval required (e.g., over threshold)
        order.approval_required = self._check_approval_required(order)

        self.db.commit()
        self.db.refresh(order)

        logger.info(f"Created PO: {order.order_number}")
        return order

    def _check_approval_required(self, order: PurchaseOrder) -> bool:
        """Check if order requires approval."""
        # Example: Orders over 10,000 require approval
        APPROVAL_THRESHOLD = Decimal("10000")
        return order.total_amount > APPROVAL_THRESHOLD

    def update_order(
        self,
        order_id: UUID,
        data: PurchaseOrderUpdate,
    ) -> PurchaseOrder:
        """Update purchase order."""
        order = self.db.query(PurchaseOrder).get(order_id)
        if not order:
            raise ValueError("Order not found")

        if not order.is_editable:
            raise ValueError(f"Order cannot be edited in status: {order.status}")

        # Update fields
        for field, value in data.dict(exclude_unset=True).items():
            if value is not None:
                setattr(order, field, value)

        # Recalculate totals if amounts changed
        if data.discount_amount is not None or data.shipping_amount is not None:
            order.recalculate_totals()

        self.db.commit()
        self.db.refresh(order)

        return order

    def add_line(
        self,
        order_id: UUID,
        data: AddLineRequest,
    ) -> PurchaseOrderLine:
        """Add line to existing order."""
        order = self.db.query(PurchaseOrder).get(order_id)
        if not order:
            raise ValueError("Order not found")

        if not order.is_editable:
            raise ValueError("Order cannot be edited")

        product = self.db.query(Product).get(data.product_id)
        if not product:
            raise ValueError("Product not found")

        # Get next line number
        max_line = max((l.line_number for l in order.lines), default=0)

        # Get price
        unit_price = data.unit_price
        if unit_price is None:
            unit_price = self._get_product_price(
                order.supplier_id, data.product_id, data.quantity
            )
        if unit_price is None:
            unit_price = product.standard_cost or Decimal("0")

        line = PurchaseOrderLine(
            order_id=order_id,
            line_number=max_line + 1,
            product_id=data.product_id,
            description=product.name,
            quantity=data.quantity,
            uom_id=product.uom_id,
            unit_price=unit_price,
            discount_percent=data.discount_percent,
            tax_rate=data.tax_rate,
            expected_date=data.expected_date or order.expected_date,
            warehouse_id=order.delivery_warehouse_id,
            notes=data.notes,
        )
        line.calculate_amounts()

        self.db.add(line)
        self.db.flush()

        order.recalculate_totals()
        self.db.commit()
        self.db.refresh(line)

        return line

    def update_line(
        self,
        line_id: UUID,
        data: OrderLineUpdate,
    ) -> PurchaseOrderLine:
        """Update order line."""
        line = self.db.query(PurchaseOrderLine).get(line_id)
        if not line:
            raise ValueError("Line not found")

        if not line.order.is_editable:
            raise ValueError("Order cannot be edited")

        for field, value in data.dict(exclude_unset=True).items():
            if value is not None:
                setattr(line, field, value)

        line.calculate_amounts()
        self.db.flush()

        line.order.recalculate_totals()
        self.db.commit()
        self.db.refresh(line)

        return line

    def delete_line(self, line_id: UUID) -> bool:
        """Delete order line."""
        line = self.db.query(PurchaseOrderLine).get(line_id)
        if not line:
            return False

        if not line.order.is_editable:
            raise ValueError("Order cannot be edited")

        order = line.order
        self.db.delete(line)
        self.db.flush()

        order.recalculate_totals()
        self.db.commit()

        return True

    def submit_for_approval(self, order_id: UUID) -> PurchaseOrder:
        """Submit order for approval."""
        order = self.db.query(PurchaseOrder).get(order_id)
        if not order:
            raise ValueError("Order not found")

        if order.status != POStatusEnum.DRAFT.value:
            raise ValueError("Only draft orders can be submitted")

        if not order.lines:
            raise ValueError("Order has no lines")

        if order.approval_required:
            order.status = POStatusEnum.PENDING_APPROVAL.value
            order.approval_status = "pending"
        else:
            order.status = POStatusEnum.APPROVED.value
            order.approval_status = "auto_approved"

        self.db.commit()
        self.db.refresh(order)

        return order

    def approve_order(
        self,
        order_id: UUID,
        approver_id: UUID,
        action: str,
        comments: str = None,
    ) -> PurchaseOrder:
        """Approve, reject, or return order."""
        order = self.db.query(PurchaseOrder).get(order_id)
        if not order:
            raise ValueError("Order not found")

        if order.status != POStatusEnum.PENDING_APPROVAL.value:
            raise ValueError("Order is not pending approval")

        # Record approval action
        approval = PurchaseOrderApproval(
            order_id=order_id,
            approver_id=approver_id,
            action=action,
            comments=comments,
        )
        self.db.add(approval)

        if action == "approve":
            order.status = POStatusEnum.APPROVED.value
            order.approval_status = "approved"
            order.approved_by = approver_id
            order.approved_at = datetime.utcnow()
        elif action == "reject":
            order.status = POStatusEnum.CANCELLED.value
            order.approval_status = "rejected"
        elif action == "return":
            order.status = POStatusEnum.DRAFT.value
            order.approval_status = "returned"

        self.db.commit()
        self.db.refresh(order)

        return order

    def send_order(self, order_id: UUID) -> PurchaseOrder:
        """Mark order as sent to supplier."""
        order = self.db.query(PurchaseOrder).get(order_id)
        if not order:
            raise ValueError("Order not found")

        if order.status != POStatusEnum.APPROVED.value:
            raise ValueError("Order must be approved first")

        order.status = POStatusEnum.SENT.value
        self.db.commit()
        self.db.refresh(order)

        return order

    def cancel_order(
        self,
        order_id: UUID,
        reason: str,
    ) -> PurchaseOrder:
        """Cancel order."""
        order = self.db.query(PurchaseOrder).get(order_id)
        if not order:
            raise ValueError("Order not found")

        # Cannot cancel if already received
        if order.received_amount > 0:
            raise ValueError("Cannot cancel order with receipts")

        order.status = POStatusEnum.CANCELLED.value
        order.internal_notes = f"{order.internal_notes or ''}\nCancelled: {reason}".strip()

        # Cancel all lines
        for line in order.lines:
            line.status = POLineStatusEnum.CANCELLED.value

        self.db.commit()
        self.db.refresh(order)

        return order

    def get_order_by_id(self, order_id: UUID) -> Optional[PurchaseOrder]:
        """Get order by ID."""
        return self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.supplier),
            joinedload(PurchaseOrder.lines).joinedload(PurchaseOrderLine.product),
            joinedload(PurchaseOrder.delivery_warehouse),
            joinedload(PurchaseOrder.payment_term),
        ).get(order_id)

    def get_orders(
        self,
        customer_id: UUID,
        filters: PurchaseOrderFilter = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[PurchaseOrder], int]:
        """Get orders with filtering."""
        query = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.customer_id == customer_id
        )

        if filters:
            if filters.supplier_id:
                query = query.filter(PurchaseOrder.supplier_id == filters.supplier_id)

            if filters.status:
                query = query.filter(PurchaseOrder.status == filters.status.value)

            if filters.date_from:
                query = query.filter(PurchaseOrder.order_date >= filters.date_from)

            if filters.date_to:
                query = query.filter(PurchaseOrder.order_date <= filters.date_to)

            if filters.warehouse_id:
                query = query.filter(PurchaseOrder.delivery_warehouse_id == filters.warehouse_id)

            if filters.search:
                search = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        PurchaseOrder.order_number.ilike(search),
                        PurchaseOrder.reference.ilike(search),
                    )
                )

            if filters.has_pending_receipt:
                query = query.filter(
                    PurchaseOrder.status.in_([
                        POStatusEnum.APPROVED.value,
                        POStatusEnum.SENT.value,
                        POStatusEnum.PARTIAL.value,
                    ])
                )

        total = query.count()

        orders = query.options(
            joinedload(PurchaseOrder.supplier),
        ).order_by(
            PurchaseOrder.order_date.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return orders, total

    def get_dashboard_stats(self, customer_id: UUID) -> dict:
        """Get dashboard statistics."""
        today = date.today()
        month_start = today.replace(day=1)

        # Counts by status
        draft_count = self.db.query(func.count(PurchaseOrder.id)).filter(
            PurchaseOrder.customer_id == customer_id,
            PurchaseOrder.status == POStatusEnum.DRAFT.value,
        ).scalar()

        pending_approval = self.db.query(func.count(PurchaseOrder.id)).filter(
            PurchaseOrder.customer_id == customer_id,
            PurchaseOrder.status == POStatusEnum.PENDING_APPROVAL.value,
        ).scalar()

        pending_receipt = self.db.query(func.count(PurchaseOrder.id)).filter(
            PurchaseOrder.customer_id == customer_id,
            PurchaseOrder.status.in_([
                POStatusEnum.APPROVED.value,
                POStatusEnum.SENT.value,
                POStatusEnum.PARTIAL.value,
            ]),
        ).scalar()

        # This month
        month_stats = self.db.query(
            func.count(PurchaseOrder.id),
            func.coalesce(func.sum(PurchaseOrder.total_amount), 0),
        ).filter(
            PurchaseOrder.customer_id == customer_id,
            PurchaseOrder.order_date >= month_start,
            PurchaseOrder.status != POStatusEnum.CANCELLED.value,
        ).first()

        # Top suppliers
        top_suppliers = self.db.query(
            Supplier.name,
            func.count(PurchaseOrder.id).label("order_count"),
            func.sum(PurchaseOrder.total_amount).label("total_amount"),
        ).join(
            PurchaseOrder, Supplier.id == PurchaseOrder.supplier_id
        ).filter(
            PurchaseOrder.customer_id == customer_id,
            PurchaseOrder.order_date >= month_start,
            PurchaseOrder.status != POStatusEnum.CANCELLED.value,
        ).group_by(Supplier.name).order_by(
            func.sum(PurchaseOrder.total_amount).desc()
        ).limit(5).all()

        return {
            "total_draft": draft_count,
            "total_pending_approval": pending_approval,
            "total_pending_receipt": pending_receipt,
            "total_this_month": month_stats[0],
            "amount_this_month": float(month_stats[1]),
            "top_suppliers": [
                {
                    "name": s.name,
                    "order_count": s.order_count,
                    "total_amount": float(s.total_amount),
                }
                for s in top_suppliers
            ],
        }


def get_purchase_order_service(db: Session) -> PurchaseOrderService:
    """Factory function."""
    return PurchaseOrderService(db)
