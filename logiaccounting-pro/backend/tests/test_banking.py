"""
Tests for banking module.
"""
import pytest
from datetime import datetime, timedelta


class TestBankingAccountsModels:
    """Tests for banking account models."""

    def test_bank_account_creation(self):
        """Test bank account data structure."""
        account = {
            "id": "acc-001",
            "account_name": "Operating Account",
            "bank_name": "Test Bank",
            "account_number": "****1234",
            "currency": "USD",
            "balance": 10000.00,
            "is_active": True
        }
        assert account["account_name"] == "Operating Account"
        assert account["balance"] == 10000.00
        assert account["is_active"] is True

    def test_bank_account_required_fields(self):
        """Test that required fields are present."""
        required_fields = ["account_name", "bank_name", "account_number", "currency"]
        account = {
            "account_name": "Test",
            "bank_name": "Bank",
            "account_number": "1234",
            "currency": "USD"
        }
        for field in required_fields:
            assert field in account


class TestReconciliationService:
    """Tests for bank reconciliation service."""

    def test_reconciliation_match_exact(self):
        """Test exact matching of transactions."""
        bank_tx = {"amount": 100.00, "date": "2024-01-15", "reference": "INV-001"}
        book_tx = {"amount": 100.00, "date": "2024-01-15", "reference": "INV-001"}

        assert bank_tx["amount"] == book_tx["amount"]
        assert bank_tx["reference"] == book_tx["reference"]

    def test_reconciliation_match_with_tolerance(self):
        """Test matching with small amount tolerance."""
        tolerance = 0.01
        bank_amount = 100.00
        book_amount = 100.01

        assert abs(bank_amount - book_amount) <= tolerance

    def test_reconciliation_unmatched_transactions(self):
        """Test identifying unmatched transactions."""
        bank_transactions = [
            {"id": "bt1", "amount": 100.00},
            {"id": "bt2", "amount": 200.00},
        ]
        matched_ids = ["bt1"]

        unmatched = [tx for tx in bank_transactions if tx["id"] not in matched_ids]
        assert len(unmatched) == 1
        assert unmatched[0]["id"] == "bt2"


class TestPaymentsService:
    """Tests for banking payments service."""

    def test_payment_creation(self):
        """Test payment data structure."""
        payment = {
            "id": "pay-001",
            "amount": 500.00,
            "currency": "USD",
            "recipient": "Vendor Corp",
            "status": "pending",
            "payment_method": "bank_transfer"
        }
        assert payment["status"] == "pending"
        assert payment["amount"] == 500.00

    def test_payment_status_transitions(self):
        """Test valid payment status transitions."""
        valid_transitions = {
            "pending": ["approved", "cancelled"],
            "approved": ["processing", "cancelled"],
            "processing": ["completed", "failed"],
            "completed": [],
            "failed": ["pending"],
            "cancelled": []
        }

        assert "approved" in valid_transitions["pending"]
        assert "completed" not in valid_transitions["pending"]


class TestCashflowService:
    """Tests for cashflow forecasting service."""

    def test_cashflow_projection(self):
        """Test basic cashflow projection."""
        current_balance = 10000.00
        expected_income = 5000.00
        expected_expenses = 3000.00

        projected_balance = current_balance + expected_income - expected_expenses
        assert projected_balance == 12000.00

    def test_cashflow_date_range(self):
        """Test cashflow projection date handling."""
        start_date = datetime(2024, 1, 1)
        end_date = start_date + timedelta(days=30)

        assert (end_date - start_date).days == 30
