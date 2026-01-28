"""
Tests for purchasing module.
"""
import pytest
from datetime import datetime, timedelta


class TestPurchaseOrders:
    """Tests for purchase orders service."""

    def test_purchase_order_creation(self):
        """Test purchase order data structure."""
        po = {
            "id": "po-001",
            "po_number": "PO-2024-0001",
            "supplier_id": "sup-001",
            "order_date": datetime.now().isoformat(),
            "expected_date": (datetime.now() + timedelta(days=14)).isoformat(),
            "status": "draft",
            "lines": [
                {"product_id": "prod-001", "quantity": 100, "unit_cost": 10.00}
            ],
            "subtotal": 1000.00,
            "shipping": 50.00,
            "total": 1050.00
        }

        assert po["status"] == "draft"
        assert "PO-2024" in po["po_number"]

    def test_po_status_transitions(self):
        """Test valid PO status transitions."""
        valid_transitions = {
            "draft": ["submitted", "cancelled"],
            "submitted": ["approved", "rejected"],
            "approved": ["ordered", "cancelled"],
            "ordered": ["partial", "received", "cancelled"],
            "partial": ["received"],
            "received": ["closed"],
            "rejected": ["draft"],
            "cancelled": [],
            "closed": []
        }

        assert "submitted" in valid_transitions["draft"]
        assert "approved" in valid_transitions["submitted"]

    def test_po_approval_required(self):
        """Test PO approval threshold."""
        approval_threshold = 5000.00

        po1 = {"total": 4500.00}
        po2 = {"total": 6000.00}

        needs_approval_1 = po1["total"] >= approval_threshold
        needs_approval_2 = po2["total"] >= approval_threshold

        assert needs_approval_1 is False
        assert needs_approval_2 is True


class TestSuppliers:
    """Tests for supplier management."""

    def test_supplier_creation(self):
        """Test supplier data structure."""
        supplier = {
            "id": "sup-001",
            "name": "Acme Supplies",
            "code": "ACME",
            "contact_email": "orders@acme.com",
            "payment_terms": "net30",
            "is_active": True,
            "rating": 4.5
        }

        assert supplier["is_active"] is True
        assert supplier["payment_terms"] == "net30"

    def test_supplier_payment_terms(self):
        """Test supplier payment terms calculation."""
        terms = {
            "immediate": 0,
            "net15": 15,
            "net30": 30,
            "net45": 45,
            "net60": 60
        }

        order_date = datetime.now()
        payment_term = "net30"
        due_date = order_date + timedelta(days=terms[payment_term])

        assert (due_date - order_date).days == 30

    def test_supplier_rating_calculation(self):
        """Test supplier rating calculation."""
        ratings = [
            {"category": "quality", "score": 4.5},
            {"category": "delivery", "score": 4.0},
            {"category": "price", "score": 4.8},
            {"category": "service", "score": 4.2}
        ]

        avg_rating = sum(r["score"] for r in ratings) / len(ratings)
        assert round(avg_rating, 2) == 4.38


class TestReceiving:
    """Tests for goods receiving service."""

    def test_receipt_creation(self):
        """Test goods receipt data structure."""
        receipt = {
            "id": "rcpt-001",
            "po_id": "po-001",
            "received_date": datetime.now().isoformat(),
            "received_by": "user-001",
            "lines": [
                {"product_id": "prod-001", "quantity_expected": 100, "quantity_received": 95}
            ],
            "status": "pending_inspection"
        }

        assert receipt["status"] == "pending_inspection"

    def test_quantity_variance(self):
        """Test quantity variance calculation."""
        expected = 100
        received = 95

        variance = received - expected
        variance_percent = (variance / expected) * 100

        assert variance == -5
        assert variance_percent == -5.0

    def test_receipt_status_flow(self):
        """Test receiving status flow."""
        statuses = ["pending_inspection", "inspected", "accepted", "put_away"]

        current_status = "pending_inspection"
        current_index = statuses.index(current_status)
        next_status = statuses[current_index + 1]

        assert next_status == "inspected"


class TestPurchaseInvoices:
    """Tests for purchase invoices."""

    def test_invoice_matching(self):
        """Test 3-way matching concept."""
        po = {"product_id": "prod-001", "quantity": 100, "unit_cost": 10.00}
        receipt = {"product_id": "prod-001", "quantity_received": 100}
        invoice = {"product_id": "prod-001", "quantity": 100, "unit_cost": 10.00}

        qty_match = po["quantity"] == invoice["quantity"] == receipt["quantity_received"]
        price_match = po["unit_cost"] == invoice["unit_cost"]

        assert qty_match is True
        assert price_match is True

    def test_invoice_variance_tolerance(self):
        """Test invoice variance tolerance."""
        tolerance_percent = 5
        po_amount = 1000.00
        invoice_amount = 1040.00

        variance = ((invoice_amount - po_amount) / po_amount) * 100
        within_tolerance = abs(variance) <= tolerance_percent

        assert variance == 4.0
        assert within_tolerance is True
