"""
Supplier Invoice Service
3-way matching and invoice processing
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.purchasing.invoices.models import (
    SupplierInvoice, SupplierInvoiceLine,
    InvoiceStatusEnum, MatchStatusEnum
)
from app.purchasing.orders.models import PurchaseOrder, PurchaseOrderLine, POStatusEnum
from app.purchasing.receiving.models import GoodsReceipt, GoodsReceiptLine

logger = logging.getLogger(__name__)


class SupplierInvoiceService:
    """Service for supplier invoices."""

    def __init__(self, db: Session):
        self.db = db

    def _generate_invoice_number(self, customer_id: UUID) -> str:
        year = datetime.utcnow().strftime("%y")

        last = self.db.query(SupplierInvoice).filter(
            SupplierInvoice.customer_id == customer_id,
            SupplierInvoice.invoice_number.like(f"SINV-{year}%")
        ).order_by(SupplierInvoice.invoice_number.desc()).first()

        if last:
            try:
                last_num = int(last.invoice_number.split("-")[-1])
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1

        return f"SINV-{year}-{next_num:06d}"

    def create_invoice(
        self,
        customer_id: UUID,
        supplier_id: UUID,
        invoice_date: date,
        due_date: date,
        lines: List[dict],
        supplier_invoice_number: str = None,
        currency: str = "USD",
        discount_amount: Decimal = None,
        notes: str = None,
        created_by: UUID = None,
    ) -> SupplierInvoice:
        """Create supplier invoice."""
        invoice = SupplierInvoice(
            customer_id=customer_id,
            invoice_number=self._generate_invoice_number(customer_id),
            supplier_id=supplier_id,
            supplier_invoice_number=supplier_invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            posting_date=date.today(),
            currency=currency,
            discount_amount=discount_amount or Decimal("0"),
            notes=notes,
            created_by=created_by,
        )

        self.db.add(invoice)
        self.db.flush()

        # Add lines
        for idx, line_data in enumerate(lines, start=1):
            line = SupplierInvoiceLine(
                invoice_id=invoice.id,
                line_number=idx,
                order_line_id=line_data.get("order_line_id"),
                receipt_line_id=line_data.get("receipt_line_id"),
                product_id=line_data.get("product_id"),
                description=line_data["description"],
                account_id=line_data.get("account_id"),
                quantity=line_data["quantity"],
                unit_price=line_data["unit_price"],
                discount_percent=line_data.get("discount_percent", Decimal("0")),
                tax_rate=line_data.get("tax_rate", Decimal("0")),
            )
            line.calculate_amounts()
            self.db.add(line)

        self.db.flush()
        invoice.recalculate_totals()

        self.db.commit()
        self.db.refresh(invoice)

        return invoice

    def create_invoice_from_receipt(
        self,
        customer_id: UUID,
        receipt_id: UUID,
        supplier_invoice_number: str = None,
        invoice_date: date = None,
        due_date: date = None,
        created_by: UUID = None,
    ) -> SupplierInvoice:
        """Create invoice from goods receipt."""
        receipt = self.db.query(GoodsReceipt).options(
            joinedload(GoodsReceipt.lines),
            joinedload(GoodsReceipt.supplier),
        ).get(receipt_id)

        if not receipt:
            raise ValueError("Receipt not found")

        # Calculate due date from supplier payment terms if not provided
        supplier = receipt.supplier
        if not due_date:
            due_date = (invoice_date or date.today()) + timedelta(days=30)

        lines = []
        for rl in receipt.lines:
            lines.append({
                "order_line_id": rl.order_line_id,
                "receipt_line_id": rl.id,
                "product_id": rl.product_id,
                "description": rl.product.name if rl.product else "Product",
                "quantity": rl.quantity_received,
                "unit_price": rl.unit_cost or Decimal("0"),
            })

        invoice = self.create_invoice(
            customer_id=customer_id,
            supplier_id=receipt.supplier_id,
            invoice_date=invoice_date or date.today(),
            due_date=due_date,
            lines=lines,
            supplier_invoice_number=supplier_invoice_number,
            created_by=created_by,
        )

        # Auto-match since created from receipt
        self.perform_3way_match(invoice.id)

        return invoice

    def perform_3way_match(self, invoice_id: UUID) -> dict:
        """Perform 3-way matching (PO ↔ Receipt ↔ Invoice)."""
        invoice = self.db.query(SupplierInvoice).options(
            joinedload(SupplierInvoice.lines)
        ).get(invoice_id)

        if not invoice:
            raise ValueError("Invoice not found")

        match_results = {
            "total_lines": len(invoice.lines),
            "matched": 0,
            "exceptions": 0,
            "variances": [],
        }

        for line in invoice.lines:
            if not line.order_line_id and not line.receipt_line_id:
                # No reference - cannot match
                line.match_status = "unmatched"
                continue

            # Get PO and receipt data
            po_line = None
            receipt_line = None

            if line.order_line_id:
                po_line = self.db.query(PurchaseOrderLine).get(line.order_line_id)

            if line.receipt_line_id:
                receipt_line = self.db.query(GoodsReceiptLine).get(line.receipt_line_id)

            # Calculate variances
            price_variance = Decimal("0")
            qty_variance = Decimal("0")

            if po_line:
                # Price variance: Invoice price vs PO price
                price_variance = line.unit_price - po_line.unit_price

            if receipt_line:
                # Quantity variance: Invoice qty vs received qty
                qty_variance = line.quantity - receipt_line.quantity_received

            line.price_variance = price_variance
            line.quantity_variance = qty_variance

            # Determine match status
            PRICE_TOLERANCE = Decimal("0.01")  # 1 cent
            QTY_TOLERANCE = Decimal("0.001")   # Small rounding

            if abs(price_variance) <= PRICE_TOLERANCE and abs(qty_variance) <= QTY_TOLERANCE:
                line.match_status = "matched"
                match_results["matched"] += 1
            else:
                line.match_status = "exception"
                match_results["exceptions"] += 1
                match_results["variances"].append({
                    "line_number": line.line_number,
                    "price_variance": float(price_variance),
                    "quantity_variance": float(qty_variance),
                })

        # Update invoice match status
        if match_results["exceptions"] == 0 and match_results["matched"] > 0:
            invoice.match_status = MatchStatusEnum.MATCHED.value
        elif match_results["matched"] > 0:
            invoice.match_status = MatchStatusEnum.EXCEPTION.value
        else:
            invoice.match_status = MatchStatusEnum.UNMATCHED.value

        self.db.commit()

        return match_results

    def approve_invoice(
        self,
        invoice_id: UUID,
        approved_by: UUID,
    ) -> SupplierInvoice:
        """Approve invoice for payment."""
        invoice = self.db.query(SupplierInvoice).get(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")

        if invoice.status not in [InvoiceStatusEnum.DRAFT.value, InvoiceStatusEnum.PENDING_APPROVAL.value]:
            raise ValueError(f"Cannot approve invoice in status: {invoice.status}")

        invoice.status = InvoiceStatusEnum.APPROVED.value
        invoice.approved_by = approved_by
        invoice.approved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(invoice)

        return invoice

    def post_invoice(
        self,
        invoice_id: UUID,
        posted_by: UUID = None,
    ) -> SupplierInvoice:
        """Post invoice - create AP journal entry."""
        invoice = self.db.query(SupplierInvoice).options(
            joinedload(SupplierInvoice.lines),
            joinedload(SupplierInvoice.supplier),
        ).get(invoice_id)

        if not invoice:
            raise ValueError("Invoice not found")

        if invoice.status != InvoiceStatusEnum.APPROVED.value:
            raise ValueError("Invoice must be approved before posting")

        invoice.status = InvoiceStatusEnum.POSTED.value

        # Update PO invoiced amounts
        for line in invoice.lines:
            if line.order_line_id:
                po_line = self.db.query(PurchaseOrderLine).get(line.order_line_id)
                if po_line:
                    po_line.quantity_invoiced = (po_line.quantity_invoiced or Decimal("0")) + line.quantity

                    # Update PO
                    po = po_line.order
                    po.invoiced_amount = (po.invoiced_amount or Decimal("0")) + line.line_total
                    if po.fully_invoiced:
                        po.status = POStatusEnum.INVOICED.value

        self.db.commit()
        self.db.refresh(invoice)

        logger.info(f"Posted invoice: {invoice.invoice_number}")
        return invoice

    def record_payment(
        self,
        invoice_id: UUID,
        amount: Decimal,
        payment_date: date = None,
        payment_reference: str = None,
    ) -> SupplierInvoice:
        """Record payment against invoice."""
        invoice = self.db.query(SupplierInvoice).get(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")

        if invoice.status not in [InvoiceStatusEnum.POSTED.value, InvoiceStatusEnum.PARTIAL_PAID.value]:
            raise ValueError("Invoice must be posted to receive payment")

        invoice.amount_paid = (invoice.amount_paid or Decimal("0")) + amount

        if invoice.amount_paid >= invoice.total_amount:
            invoice.status = InvoiceStatusEnum.PAID.value
        else:
            invoice.status = InvoiceStatusEnum.PARTIAL_PAID.value

        self.db.commit()
        self.db.refresh(invoice)

        return invoice

    def get_invoice_by_id(self, invoice_id: UUID) -> Optional[SupplierInvoice]:
        """Get invoice by ID with lines."""
        return self.db.query(SupplierInvoice).options(
            joinedload(SupplierInvoice.lines).joinedload(SupplierInvoiceLine.product),
            joinedload(SupplierInvoice.supplier),
            joinedload(SupplierInvoice.payment_term),
        ).get(invoice_id)

    def get_invoices(
        self,
        customer_id: UUID,
        supplier_id: UUID = None,
        status: str = None,
        overdue_only: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[SupplierInvoice], int]:
        """Get invoices with filtering."""
        query = self.db.query(SupplierInvoice).filter(
            SupplierInvoice.customer_id == customer_id
        )

        if supplier_id:
            query = query.filter(SupplierInvoice.supplier_id == supplier_id)

        if status:
            query = query.filter(SupplierInvoice.status == status)

        if overdue_only:
            query = query.filter(
                SupplierInvoice.due_date < date.today(),
                SupplierInvoice.status.in_([
                    InvoiceStatusEnum.POSTED.value,
                    InvoiceStatusEnum.PARTIAL_PAID.value,
                ]),
            )

        total = query.count()

        invoices = query.options(
            joinedload(SupplierInvoice.supplier),
        ).order_by(
            SupplierInvoice.due_date.asc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return invoices, total

    def get_ap_aging(self, customer_id: UUID) -> dict:
        """Get accounts payable aging report."""
        today = date.today()

        invoices = self.db.query(SupplierInvoice).filter(
            SupplierInvoice.customer_id == customer_id,
            SupplierInvoice.status.in_([
                InvoiceStatusEnum.POSTED.value,
                InvoiceStatusEnum.PARTIAL_PAID.value,
            ]),
        ).all()

        aging = {
            "current": Decimal("0"),
            "days_1_30": Decimal("0"),
            "days_31_60": Decimal("0"),
            "days_61_90": Decimal("0"),
            "over_90": Decimal("0"),
            "total": Decimal("0"),
        }

        for inv in invoices:
            due = inv.amount_due or Decimal("0")
            days_overdue = (today - inv.due_date).days

            if days_overdue <= 0:
                aging["current"] += due
            elif days_overdue <= 30:
                aging["days_1_30"] += due
            elif days_overdue <= 60:
                aging["days_31_60"] += due
            elif days_overdue <= 90:
                aging["days_61_90"] += due
            else:
                aging["over_90"] += due

            aging["total"] += due

        return {k: float(v) for k, v in aging.items()}


def get_supplier_invoice_service(db: Session) -> SupplierInvoiceService:
    return SupplierInvoiceService(db)
