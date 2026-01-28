"""
Payment Portal Service
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import logging

from app.models.store import db
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class PortalPaymentService:
    def __init__(self):
        self._saved_methods: Dict[str, List[Dict]] = {}
        self._auto_pay: Dict[str, Dict] = {}

    def get_invoices(self, customer_id: str, status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        invoices = [i for i in db.invoices.find_all() if i.get("client_id") == customer_id]
        if status:
            if status == "unpaid":
                invoices = [i for i in invoices if i.get("status") in ["pending", "overdue"]]
            else:
                invoices = [i for i in invoices if i.get("status") == status]
        invoices.sort(key=lambda i: i.get("created_at", ""), reverse=True)
        total = len(invoices)
        skip = (page - 1) * page_size
        invoices = invoices[skip:skip + page_size]
        return {"items": [self._invoice_to_dict(i) for i in invoices], "total": total, "page": page, "page_size": page_size}

    def get_invoice(self, invoice_id: str, customer_id: str) -> Optional[Dict]:
        invoice = db.invoices.find_by_id(invoice_id)
        if not invoice or invoice.get("client_id") != customer_id:
            return None
        return self._invoice_to_dict(invoice, include_items=True)

    def get_invoice_stats(self, customer_id: str) -> Dict[str, Any]:
        invoices = [i for i in db.invoices.find_all() if i.get("client_id") == customer_id]
        total_paid = sum(i.get("total", 0) for i in invoices if i.get("status") == "paid")
        total_pending = sum(i.get("total", 0) for i in invoices if i.get("status") == "pending")
        total_overdue = sum(i.get("total", 0) for i in invoices if i.get("status") == "overdue")
        pending_count = len([i for i in invoices if i.get("status") in ["pending", "overdue"]])
        return {"total_paid": total_paid, "total_pending": total_pending, "total_overdue": total_overdue, "pending_count": pending_count}

    def get_payment_history(self, customer_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        payments = [p for p in db.payments.find_all() if p.get("client_id") == customer_id]
        payments.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        total = len(payments)
        skip = (page - 1) * page_size
        payments = payments[skip:skip + page_size]
        return {"items": [self._payment_to_dict(p) for p in payments], "total": total, "page": page, "page_size": page_size}

    def initiate_payment(self, invoice_id: str, customer_id: str, payment_method: str, amount: float = None) -> Dict[str, Any]:
        invoice = db.invoices.find_by_id(invoice_id)
        if not invoice or invoice.get("client_id") != customer_id:
            raise ValueError("Invoice not found")
        if invoice.get("status") == "paid":
            raise ValueError("Invoice already paid")

        pay_amount = amount or invoice.get("total", 0) - invoice.get("amount_paid", 0)
        payment = {
            "id": f"pay_{uuid4().hex[:12]}",
            "invoice_id": invoice_id,
            "client_id": customer_id,
            "amount": pay_amount,
            "payment_method": payment_method,
            "status": "completed",
            "paid_at": utc_now().isoformat(),
            "transaction_id": f"txn_{uuid4().hex[:12]}",
            "created_at": utc_now().isoformat()
        }
        db.payments.create(payment)

        current_paid = invoice.get("amount_paid", 0) + pay_amount
        if current_paid >= invoice.get("total", 0):
            invoice["status"] = "paid"
            invoice["paid_at"] = utc_now().isoformat()
        invoice["amount_paid"] = current_paid
        db.invoices.update(invoice_id, invoice)

        return {"payment_id": payment["id"], "status": payment["status"], "amount": pay_amount, "transaction_id": payment["transaction_id"]}

    def get_payment_receipt(self, payment_id: str, customer_id: str) -> Optional[Dict]:
        payments = db.payments.find_all()
        payment = next((p for p in payments if p["id"] == payment_id and p.get("client_id") == customer_id), None)
        if not payment:
            return None
        invoice = db.invoices.find_by_id(payment.get("invoice_id"))
        return {
            "receipt_number": f"RCP-{payment['id'][-8:].upper()}",
            "payment_id": payment["id"],
            "transaction_id": payment.get("transaction_id"),
            "amount": payment.get("amount"),
            "payment_method": payment.get("payment_method"),
            "paid_at": payment.get("paid_at"),
            "invoice_number": invoice.get("invoice_number") if invoice else None,
            "status": payment.get("status")
        }

    def list_payment_methods(self, customer_id: str) -> List[Dict]:
        return self._saved_methods.get(customer_id, [])

    def add_payment_method(self, customer_id: str, method_type: str, details: Dict) -> Dict:
        method = {
            "id": f"pm_{uuid4().hex[:12]}",
            "type": method_type,
            "last_four": details.get("last_four", "****"),
            "brand": details.get("brand"),
            "expiry": details.get("expiry"),
            "is_default": len(self._saved_methods.get(customer_id, [])) == 0,
            "created_at": utc_now().isoformat()
        }
        if customer_id not in self._saved_methods:
            self._saved_methods[customer_id] = []
        self._saved_methods[customer_id].append(method)
        return method

    def remove_payment_method(self, customer_id: str, method_id: str):
        methods = self._saved_methods.get(customer_id, [])
        self._saved_methods[customer_id] = [m for m in methods if m["id"] != method_id]

    def get_auto_pay(self, customer_id: str) -> Optional[Dict]:
        return self._auto_pay.get(customer_id)

    def setup_auto_pay(self, customer_id: str, payment_method_id: str, enabled: bool = True) -> Dict:
        self._auto_pay[customer_id] = {"enabled": enabled, "payment_method_id": payment_method_id, "created_at": utc_now().isoformat()}
        return self._auto_pay[customer_id]

    def disable_auto_pay(self, customer_id: str):
        if customer_id in self._auto_pay:
            self._auto_pay[customer_id]["enabled"] = False

    def get_statement(self, customer_id: str, start_date: str, end_date: str) -> Dict:
        invoices = [i for i in db.invoices.find_all() if i.get("client_id") == customer_id and start_date <= i.get("created_at", "")[:10] <= end_date]
        payments = [p for p in db.payments.find_all() if p.get("client_id") == customer_id and start_date <= p.get("created_at", "")[:10] <= end_date]
        total_invoiced = sum(i.get("total", 0) for i in invoices)
        total_paid = sum(p.get("amount", 0) for p in payments if p.get("status") == "completed")
        return {
            "period": {"start": start_date, "end": end_date},
            "summary": {"total_invoiced": total_invoiced, "total_paid": total_paid, "balance": total_invoiced - total_paid},
            "invoices": [self._invoice_to_dict(i) for i in invoices],
            "payments": [self._payment_to_dict(p) for p in payments]
        }

    def _invoice_to_dict(self, invoice: Dict, include_items: bool = False) -> Dict:
        result = {
            "id": invoice["id"],
            "invoice_number": invoice.get("invoice_number", invoice["id"][:8]),
            "status": invoice.get("status"),
            "total": invoice.get("total", 0),
            "amount_paid": invoice.get("amount_paid", 0),
            "amount_due": invoice.get("total", 0) - invoice.get("amount_paid", 0),
            "issue_date": invoice.get("created_at"),
            "due_date": invoice.get("due_date"),
            "paid_at": invoice.get("paid_at"),
            "is_overdue": invoice.get("status") == "overdue"
        }
        if include_items:
            result["items"] = invoice.get("items", [])
        return result

    def _payment_to_dict(self, payment: Dict) -> Dict:
        return {
            "id": payment["id"],
            "invoice_id": payment.get("invoice_id"),
            "amount": payment.get("amount", 0),
            "payment_method": payment.get("payment_method"),
            "status": payment.get("status"),
            "transaction_id": payment.get("transaction_id"),
            "paid_at": payment.get("paid_at"),
            "created_at": payment.get("created_at")
        }


portal_payment_service = PortalPaymentService()
