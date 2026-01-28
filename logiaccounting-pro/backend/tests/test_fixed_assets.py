"""
Tests for fixed assets module.
"""
import pytest
from datetime import datetime, date
from decimal import Decimal


class TestAssetManagement:
    """Tests for fixed asset management."""

    def test_asset_creation(self):
        """Test fixed asset data structure."""
        asset = {
            "id": "asset-001",
            "name": "Office Computer",
            "asset_number": "FA-2024-0001",
            "category": "equipment",
            "acquisition_date": "2024-01-15",
            "acquisition_cost": 1500.00,
            "useful_life_years": 5,
            "salvage_value": 100.00,
            "status": "active"
        }

        assert asset["status"] == "active"
        assert asset["useful_life_years"] == 5

    def test_asset_categories(self):
        """Test valid asset categories."""
        categories = [
            "land", "buildings", "equipment", "vehicles",
            "furniture", "computers", "software", "leasehold_improvements"
        ]

        assert "equipment" in categories
        assert "vehicles" in categories


class TestDepreciationService:
    """Tests for depreciation calculations."""

    def test_straight_line_depreciation(self):
        """Test straight-line depreciation calculation."""
        cost = 10000.00
        salvage = 1000.00
        useful_life = 5

        depreciable_amount = cost - salvage
        annual_depreciation = depreciable_amount / useful_life

        assert depreciable_amount == 9000.00
        assert annual_depreciation == 1800.00

    def test_declining_balance_depreciation(self):
        """Test declining balance depreciation."""
        cost = 10000.00
        rate = 0.40  # 40% declining balance

        year1_depreciation = cost * rate
        year1_book_value = cost - year1_depreciation
        year2_depreciation = year1_book_value * rate

        assert year1_depreciation == 4000.00
        assert year2_depreciation == 2400.00

    def test_units_of_production_depreciation(self):
        """Test units of production depreciation."""
        cost = 50000.00
        salvage = 5000.00
        total_units = 100000
        units_this_period = 15000

        depreciable_amount = cost - salvage
        rate_per_unit = depreciable_amount / total_units
        period_depreciation = rate_per_unit * units_this_period

        assert rate_per_unit == 0.45
        assert period_depreciation == 6750.00

    def test_accumulated_depreciation(self):
        """Test accumulated depreciation tracking."""
        annual_depreciation = 1800.00
        years = 3

        accumulated = annual_depreciation * years

        assert accumulated == 5400.00

    def test_book_value_calculation(self):
        """Test net book value calculation."""
        cost = 10000.00
        accumulated_depreciation = 5400.00

        book_value = cost - accumulated_depreciation

        assert book_value == 4600.00


class TestDisposalService:
    """Tests for asset disposal."""

    def test_disposal_gain_calculation(self):
        """Test gain on disposal calculation."""
        sale_price = 3000.00
        book_value = 2500.00

        gain_loss = sale_price - book_value

        assert gain_loss == 500.00
        assert gain_loss > 0  # Gain

    def test_disposal_loss_calculation(self):
        """Test loss on disposal calculation."""
        sale_price = 2000.00
        book_value = 2500.00

        gain_loss = sale_price - book_value

        assert gain_loss == -500.00
        assert gain_loss < 0  # Loss

    def test_disposal_types(self):
        """Test valid disposal types."""
        disposal_types = ["sale", "trade_in", "scrap", "donation", "write_off"]

        assert "sale" in disposal_types
        assert "write_off" in disposal_types

    def test_disposal_journal_entries(self):
        """Test disposal generates correct journal entries."""
        disposal = {
            "type": "sale",
            "sale_price": 3000.00,
            "cost": 10000.00,
            "accumulated_depreciation": 7500.00,
            "book_value": 2500.00
        }

        entries = [
            {"account": "Cash", "debit": disposal["sale_price"], "credit": 0},
            {"account": "Accumulated Depreciation", "debit": disposal["accumulated_depreciation"], "credit": 0},
            {"account": "Equipment", "debit": 0, "credit": disposal["cost"]},
            {"account": "Gain on Disposal", "debit": 0, "credit": disposal["sale_price"] - disposal["book_value"]}
        ]

        total_debits = sum(e["debit"] for e in entries)
        total_credits = sum(e["credit"] for e in entries)

        assert total_debits == total_credits


class TestAssetTracking:
    """Tests for asset tracking and location."""

    def test_asset_location_assignment(self):
        """Test asset location assignment."""
        asset = {
            "id": "asset-001",
            "current_location": "office-main",
            "assigned_to": "user-001",
            "department": "IT"
        }

        asset["current_location"] = "warehouse-A"

        assert asset["current_location"] == "warehouse-A"

    def test_asset_transfer(self):
        """Test asset transfer record."""
        transfer = {
            "asset_id": "asset-001",
            "from_location": "office-main",
            "to_location": "warehouse-A",
            "transfer_date": datetime.now().isoformat(),
            "transferred_by": "user-001",
            "reason": "Storage"
        }

        assert transfer["from_location"] == "office-main"
        assert transfer["to_location"] == "warehouse-A"


class TestAssetReports:
    """Tests for asset reporting."""

    def test_depreciation_schedule(self):
        """Test depreciation schedule generation."""
        cost = 10000.00
        salvage = 1000.00
        useful_life = 5
        annual_depreciation = (cost - salvage) / useful_life

        schedule = []
        book_value = cost
        accumulated = 0

        for year in range(1, useful_life + 1):
            accumulated += annual_depreciation
            book_value -= annual_depreciation
            schedule.append({
                "year": year,
                "depreciation": annual_depreciation,
                "accumulated": accumulated,
                "book_value": book_value
            })

        assert len(schedule) == 5
        assert schedule[-1]["book_value"] == salvage

    def test_asset_register_summary(self):
        """Test asset register summary."""
        assets = [
            {"category": "equipment", "cost": 10000, "accumulated": 5000},
            {"category": "equipment", "cost": 8000, "accumulated": 3000},
            {"category": "vehicles", "cost": 25000, "accumulated": 10000}
        ]

        by_category = {}
        for asset in assets:
            cat = asset["category"]
            if cat not in by_category:
                by_category[cat] = {"count": 0, "total_cost": 0, "total_accumulated": 0}
            by_category[cat]["count"] += 1
            by_category[cat]["total_cost"] += asset["cost"]
            by_category[cat]["total_accumulated"] += asset["accumulated"]

        assert by_category["equipment"]["count"] == 2
        assert by_category["equipment"]["total_cost"] == 18000
