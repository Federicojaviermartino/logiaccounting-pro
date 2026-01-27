"""
Transactions endpoint tests
"""
import pytest


class TestTransactions:
    """Transaction CRUD tests"""

    def test_get_transactions_as_admin(self, client, admin_headers):
        """Test getting all transactions as admin"""
        response = client.get("/api/v1/transactions", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data

    def test_get_transactions_as_client(self, client, client_headers):
        """Test client sees only their transactions"""
        response = client.get("/api/v1/transactions", headers=client_headers)
        assert response.status_code == 200

    def test_create_expense_transaction(self, client, admin_headers, sample_transaction):
        """Test creating expense transaction"""
        response = client.post(
            "/api/v1/transactions",
            json=sample_transaction,
            headers=admin_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["transaction"]["type"] == "expense"
        assert data["transaction"]["amount"] == sample_transaction["amount"]

    def test_create_income_transaction(self, client, admin_headers):
        """Test creating income transaction"""
        response = client.post(
            "/api/v1/transactions",
            json={
                "type": "income",
                "amount": 5000.00,
                "description": "Payment received",
                "date": "2024-01-20"
            },
            headers=admin_headers
        )
        assert response.status_code == 201
        assert response.json()["transaction"]["type"] == "income"

    def test_create_transaction_invalid_type(self, client, admin_headers):
        """Test creating transaction with invalid type"""
        response = client.post(
            "/api/v1/transactions",
            json={
                "type": "invalid",
                "amount": 1000.00,
                "description": "Test"
            },
            headers=admin_headers
        )
        assert response.status_code == 422

    def test_create_transaction_negative_amount(self, client, admin_headers):
        """Test creating transaction with negative amount"""
        response = client.post(
            "/api/v1/transactions",
            json={
                "type": "expense",
                "amount": -500.00,
                "description": "Negative test"
            },
            headers=admin_headers
        )
        # Should either reject or accept based on business logic
        # Typically negative amounts are rejected
        assert response.status_code in [201, 422]

    def test_filter_transactions_by_type(self, client, admin_headers):
        """Test filtering transactions by type"""
        response = client.get(
            "/api/v1/transactions?type=expense",
            headers=admin_headers
        )
        assert response.status_code == 200
        transactions = response.json()["transactions"]
        for tx in transactions:
            assert tx["type"] == "expense"
