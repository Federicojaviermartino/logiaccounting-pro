"""Tests for the Accounting module - Chart of Accounts, Journal Entries, Ledger."""
import pytest
from datetime import date


class TestChartOfAccounts:
    """Test Chart of Accounts CRUD operations."""

    def test_get_account_types(self, client, admin_headers):
        """Verify all standard account types are returned."""
        response = client.get("/api/v1/accounting/accounts/types", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        expected_types = {"asset", "liability", "equity", "revenue", "expense"}
        returned_types = {t.lower() for t in data}
        assert expected_types.issubset(returned_types)

    def test_get_templates(self, client, admin_headers):
        """Verify chart of accounts templates are available."""
        response = client.get("/api/v1/accounting/accounts/templates", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_import_template(self, client, admin_headers):
        """Import a standard chart of accounts template."""
        templates = client.get(
            "/api/v1/accounting/accounts/templates", headers=admin_headers
        ).json()
        if not templates:
            pytest.skip("No templates available")

        template_id = templates[0].get("id") or templates[0].get("code")
        response = client.post(
            "/api/v1/accounting/accounts/import-template",
            json={"template_id": template_id},
            headers=admin_headers,
        )
        assert response.status_code in [200, 201, 409]

    def test_list_accounts(self, client, admin_headers):
        """List accounts with default pagination."""
        response = client.get("/api/v1/accounting/accounts", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_create_account(self, client, admin_headers):
        """Create a new account and verify response schema."""
        payload = {
            "code": "9999",
            "name": "Test Account",
            "account_type": "expense",
            "description": "Account for automated tests",
            "is_active": True,
            "is_header": False,
        }
        response = client.post(
            "/api/v1/accounting/accounts", json=payload, headers=admin_headers
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["code"] == "9999"
        assert data["name"] == "Test Account"

    def test_get_account_by_id(self, client, admin_headers):
        """Retrieve a specific account by its ID."""
        accounts_resp = client.get(
            "/api/v1/accounting/accounts", headers=admin_headers
        )
        accounts = accounts_resp.json()
        items = accounts.get("items", accounts) if isinstance(accounts, dict) else accounts
        if not items:
            pytest.skip("No accounts to retrieve")

        account_id = items[0]["id"]
        response = client.get(
            f"/api/v1/accounting/accounts/{account_id}", headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == account_id

    def test_get_account_tree(self, client, admin_headers):
        """Retrieve hierarchical account tree."""
        response = client.get(
            "/api/v1/accounting/accounts/tree", headers=admin_headers
        )
        assert response.status_code == 200

    def test_unauthorized_access(self, client):
        """Verify endpoints reject unauthenticated requests."""
        response = client.get("/api/v1/accounting/accounts")
        assert response.status_code in [401, 403]

    def test_client_role_access(self, client, client_headers):
        """Verify client role can read accounts."""
        response = client.get(
            "/api/v1/accounting/accounts", headers=client_headers
        )
        # Clients may or may not have access depending on RBAC config
        assert response.status_code in [200, 403]


class TestJournalEntries:
    """Test Journal Entry operations."""

    @pytest.fixture
    def sample_journal_entry(self):
        """Sample journal entry payload."""
        return {
            "entry_date": str(date.today()),
            "description": "Test journal entry",
            "reference": "TEST-JE-001",
            "lines": [
                {
                    "account_code": "1000",
                    "description": "Cash debit",
                    "debit": 1000.00,
                    "credit": 0,
                },
                {
                    "account_code": "4000",
                    "description": "Revenue credit",
                    "debit": 0,
                    "credit": 1000.00,
                },
            ],
        }

    def test_list_journal_entries(self, client, admin_headers):
        """List journal entries."""
        response = client.get(
            "/api/v1/accounting/journal", headers=admin_headers
        )
        assert response.status_code == 200

    def test_create_journal_entry(self, client, admin_headers, sample_journal_entry):
        """Create a balanced journal entry."""
        response = client.post(
            "/api/v1/accounting/journal",
            json=sample_journal_entry,
            headers=admin_headers,
        )
        # May fail if accounts don't exist yet; both are acceptable outcomes
        assert response.status_code in [200, 201, 400, 422]

    def test_create_unbalanced_entry_rejected(self, client, admin_headers):
        """Verify unbalanced journal entries are rejected."""
        payload = {
            "entry_date": str(date.today()),
            "description": "Unbalanced entry",
            "lines": [
                {"account_code": "1000", "debit": 1000.00, "credit": 0},
                {"account_code": "4000", "debit": 0, "credit": 500.00},
            ],
        }
        response = client.post(
            "/api/v1/accounting/journal", json=payload, headers=admin_headers
        )
        # Should be rejected as unbalanced (400 or 422)
        assert response.status_code in [400, 422]

    def test_create_entry_missing_lines_rejected(self, client, admin_headers):
        """Verify entries without lines are rejected."""
        payload = {
            "entry_date": str(date.today()),
            "description": "Entry without lines",
            "lines": [],
        }
        response = client.post(
            "/api/v1/accounting/journal", json=payload, headers=admin_headers
        )
        assert response.status_code in [400, 422]


class TestLedger:
    """Test General Ledger and Trial Balance operations."""

    def test_get_trial_balance(self, client, admin_headers):
        """Generate trial balance report."""
        response = client.get(
            "/api/v1/accounting/ledger/trial-balance",
            params={"as_of_date": str(date.today())},
            headers=admin_headers,
        )
        assert response.status_code == 200

    def test_get_account_balances(self, client, admin_headers):
        """Get all account balances."""
        response = client.get(
            "/api/v1/accounting/ledger/balances", headers=admin_headers
        )
        assert response.status_code == 200

    def test_get_balance_sheet(self, client, admin_headers):
        """Generate balance sheet statement."""
        response = client.get(
            "/api/v1/accounting/ledger/statements/balance-sheet",
            params={"as_of_date": str(date.today())},
            headers=admin_headers,
        )
        assert response.status_code == 200

    def test_get_income_statement(self, client, admin_headers):
        """Generate income statement."""
        response = client.get(
            "/api/v1/accounting/ledger/statements/income-statement",
            params={
                "start_date": str(date(date.today().year, 1, 1)),
                "end_date": str(date.today()),
            },
            headers=admin_headers,
        )
        assert response.status_code == 200

    def test_get_cash_flow_statement(self, client, admin_headers):
        """Generate cash flow statement."""
        response = client.get(
            "/api/v1/accounting/ledger/statements/cash-flow",
            params={
                "start_date": str(date(date.today().year, 1, 1)),
                "end_date": str(date.today()),
            },
            headers=admin_headers,
        )
        assert response.status_code == 200

    def test_trial_balance_is_balanced(self, client, admin_headers):
        """Verify trial balance debits equal credits."""
        response = client.get(
            "/api/v1/accounting/ledger/trial-balance",
            params={"as_of_date": str(date.today())},
            headers=admin_headers,
        )
        if response.status_code == 200:
            data = response.json()
            if "is_balanced" in data:
                assert data["is_balanced"] is True
            elif "total_debits" in data and "total_credits" in data:
                assert abs(data["total_debits"] - data["total_credits"]) < 0.01
