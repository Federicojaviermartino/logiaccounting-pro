"""
Goods Receipt Service
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
import logging

from app.utils.datetime_utils import utc_now

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.purchasing.receiving.models import (
    GoodsReceipt, GoodsReceiptLine,
    ReceiptStatusEnum, QualityStatusEnum
)
from app.purchasing.orders.models import (
    PurchaseOrder, PurchaseOrderLine,
    POStatusEnum, POLineStatusEnum
)

logger = logging.getLogger(__name__)


class GoodsReceiptService:
    """Service for goods receiving."""

    def __init__(self, db: Session):
        self.db = db

    def _generate_receipt_number(self, customer_id: UUID) -> str:
        year = utc_now().strftime("%y")

        last = self.db.query(GoodsReceipt).filter(
            GoodsReceipt.customer_id == customer_id,
            GoodsReceipt.receipt_number.like(f"GR-{year}%")
        ).order_by(GoodsReceipt.receipt_number.desc()).first()

        if last:
            try:
                last_num = int(last.receipt_number.split("-")[-1])
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1

        return f"GR-{year}-{next_num:06d}"

    def create_receipt_from_po(
        self,
        customer_id: UUID,
        purchase_order_id: UUID,
        warehouse_id: UUID,
        receipt_date: date = None,
        supplier_delivery_note: str = None,
        created_by: UUID = None,
    ) -> GoodsReceipt:
        """Create receipt from purchase order with all pending lines."""
        po = self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.lines)
        ).get(purchase_order_id)

        if not po:
            raise ValueError("Purchase order not found")

        if not po.can_receive:
            raise ValueError(f"Cannot receive order in status: {po.status}")

        receipt = GoodsReceipt(
            customer_id=customer_id,
            receipt_number=self._generate_receipt_number(customer_id),
            purchase_order_id=purchase_order_id,
            supplier_id=po.supplier_id,
            receipt_date=receipt_date or date.today(),
            posting_date=receipt_date or date.today(),
            warehouse_id=warehouse_id,
            supplier_delivery_note=supplier_delivery_note,
            created_by=created_by,
        )

        self.db.add(receipt)
        self.db.flush()

        # Add lines for pending quantities
        line_num = 0
        for po_line in po.lines:
            if po_line.status == POLineStatusEnum.CANCELLED.value:
                continue

            pending = po_line.quantity - (po_line.quantity_received or Decimal("0"))
            if pending <= 0:
                continue

            line_num += 1
            line = GoodsReceiptLine(
                receipt_id=receipt.id,
                line_number=line_num,
                order_line_id=po_line.id,
                product_id=po_line.product_id,
                quantity_ordered=po_line.quantity,
                quantity_received=pending,  # Default to pending qty
                uom_id=po_line.uom_id,
                unit_cost=po_line.unit_price,
            )
            self.db.add(line)

        if line_num == 0:
            raise ValueError("No pending lines to receive")

        self.db.commit()
        self.db.refresh(receipt)

        return receipt

    def create_receipt_direct(
        self,
        customer_id: UUID,
        supplier_id: UUID,
        warehouse_id: UUID,
        lines: List[dict],
        receipt_date: date = None,
        supplier_delivery_note: str = None,
        created_by: UUID = None,
    ) -> GoodsReceipt:
        """Create receipt without PO (direct purchase)."""
        receipt = GoodsReceipt(
            customer_id=customer_id,
            receipt_number=self._generate_receipt_number(customer_id),
            supplier_id=supplier_id,
            receipt_date=receipt_date or date.today(),
            posting_date=receipt_date or date.today(),
            warehouse_id=warehouse_id,
            supplier_delivery_note=supplier_delivery_note,
            created_by=created_by,
        )

        self.db.add(receipt)
        self.db.flush()

        for idx, line_data in enumerate(lines, start=1):
            line = GoodsReceiptLine(
                receipt_id=receipt.id,
                line_number=idx,
                product_id=line_data["product_id"],
                quantity_received=line_data["quantity"],
                unit_cost=line_data.get("unit_cost", Decimal("0")),
                location_id=line_data.get("location_id"),
                lot_number=line_data.get("lot_number"),
                expiry_date=line_data.get("expiry_date"),
                serial_numbers=line_data.get("serial_numbers"),
            )
            self.db.add(line)

        self.db.commit()
        self.db.refresh(receipt)

        return receipt

    def update_receipt_line(
        self,
        line_id: UUID,
        quantity_received: Decimal = None,
        location_id: UUID = None,
        lot_number: str = None,
        expiry_date: date = None,
        serial_numbers: List[str] = None,
        quality_status: str = None,
        rejection_reason: str = None,
    ) -> GoodsReceiptLine:
        """Update receipt line before posting."""
        line = self.db.query(GoodsReceiptLine).get(line_id)
        if not line:
            raise ValueError("Line not found")

        if line.receipt.status != ReceiptStatusEnum.DRAFT.value:
            raise ValueError("Cannot edit posted receipt")

        if quantity_received is not None:
            line.quantity_received = quantity_received
        if location_id is not None:
            line.location_id = location_id
        if lot_number is not None:
            line.lot_number = lot_number
        if expiry_date is not None:
            line.expiry_date = expiry_date
        if serial_numbers is not None:
            line.serial_numbers = serial_numbers
        if quality_status is not None:
            line.quality_status = quality_status
        if rejection_reason is not None:
            line.rejection_reason = rejection_reason

        self.db.commit()
        self.db.refresh(line)

        return line

    def post_receipt(
        self,
        receipt_id: UUID,
        posted_by: UUID = None,
    ) -> GoodsReceipt:
        """Post receipt - create inventory movements."""
        receipt = self.db.query(GoodsReceipt).options(
            joinedload(GoodsReceipt.lines)
        ).get(receipt_id)

        if not receipt:
            raise ValueError("Receipt not found")

        if receipt.status != ReceiptStatusEnum.DRAFT.value:
            raise ValueError("Receipt already posted")

        # Process each line
        for line in receipt.lines:
            if line.quality_status == QualityStatusEnum.REJECTED.value:
                continue  # Skip rejected lines

            # Update PO line if linked
            if line.order_line_id:
                po_line = self.db.query(PurchaseOrderLine).get(line.order_line_id)
                if po_line:
                    po_line.quantity_received = (po_line.quantity_received or Decimal("0")) + line.quantity_received

                    # Update line status
                    if po_line.quantity_received >= po_line.quantity:
                        po_line.status = POLineStatusEnum.RECEIVED.value
                    else:
                        po_line.status = POLineStatusEnum.PARTIAL.value

        # Update PO status if linked
        if receipt.purchase_order_id:
            po = self.db.query(PurchaseOrder).get(receipt.purchase_order_id)
            if po:
                # Calculate total received
                total_received = sum(
                    l.quantity_received for l in receipt.lines
                    if l.quality_status != QualityStatusEnum.REJECTED.value
                )
                po.received_amount = (po.received_amount or Decimal("0")) + (
                    total_received * (receipt.lines[0].unit_cost or Decimal("0"))
                    if receipt.lines else Decimal("0")
                )

                # Update status
                if po.fully_received:
                    po.status = POStatusEnum.RECEIVED.value
                else:
                    po.status = POStatusEnum.PARTIAL.value

        receipt.status = ReceiptStatusEnum.POSTED.value
        receipt.posted_by = posted_by
        receipt.posted_at = utc_now()

        self.db.commit()
        self.db.refresh(receipt)

        logger.info(f"Posted receipt: {receipt.receipt_number}")
        return receipt

    def cancel_receipt(self, receipt_id: UUID, reason: str) -> GoodsReceipt:
        """Cancel a draft receipt."""
        receipt = self.db.query(GoodsReceipt).get(receipt_id)
        if not receipt:
            raise ValueError("Receipt not found")

        if receipt.status != ReceiptStatusEnum.DRAFT.value:
            raise ValueError("Only draft receipts can be cancelled")

        receipt.status = ReceiptStatusEnum.CANCELLED.value
        receipt.notes = f"{receipt.notes or ''}\nCancelled: {reason}".strip()

        self.db.commit()
        self.db.refresh(receipt)

        return receipt

    def get_receipt_by_id(self, receipt_id: UUID) -> Optional[GoodsReceipt]:
        """Get receipt by ID with lines."""
        return self.db.query(GoodsReceipt).options(
            joinedload(GoodsReceipt.lines).joinedload(GoodsReceiptLine.product),
            joinedload(GoodsReceipt.supplier),
            joinedload(GoodsReceipt.warehouse),
            joinedload(GoodsReceipt.purchase_order),
        ).get(receipt_id)

    def get_receipts(
        self,
        customer_id: UUID,
        supplier_id: UUID = None,
        purchase_order_id: UUID = None,
        status: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[GoodsReceipt], int]:
        """Get receipts with filtering."""
        query = self.db.query(GoodsReceipt).filter(
            GoodsReceipt.customer_id == customer_id
        )

        if supplier_id:
            query = query.filter(GoodsReceipt.supplier_id == supplier_id)

        if purchase_order_id:
            query = query.filter(GoodsReceipt.purchase_order_id == purchase_order_id)

        if status:
            query = query.filter(GoodsReceipt.status == status)

        total = query.count()

        receipts = query.options(
            joinedload(GoodsReceipt.supplier),
            joinedload(GoodsReceipt.warehouse),
        ).order_by(
            GoodsReceipt.receipt_date.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return receipts, total


def get_goods_receipt_service(db: Session) -> GoodsReceiptService:
    return GoodsReceiptService(db)
