"""
Tax Management Service
"""

from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal, ROUND_HALF_UP
from app.models.store import db
from app.utils.datetime_utils import utc_now


class TaxService:
    """Manages tax rates and calculations"""

    _instance = None
    _taxes: Dict[str, dict] = {}
    _counter = 0

    TAX_TYPES = ["vat", "sales_tax", "withholding", "income", "custom"]

    DEFAULT_TAXES = [
        {"name": "IVA 21%", "code": "IVA21", "type": "vat", "rate": 21.0, "is_default": True},
        {"name": "IVA 10.5%", "code": "IVA105", "type": "vat", "rate": 10.5, "is_default": False},
        {"name": "IVA 27%", "code": "IVA27", "type": "vat", "rate": 27.0, "is_default": False},
        {"name": "Exempt", "code": "EXEMPT", "type": "vat", "rate": 0.0, "is_default": False}
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._taxes = {}
            cls._counter = 0
            cls._init_default_taxes()
        return cls._instance

    @classmethod
    def _init_default_taxes(cls):
        """Initialize default tax rates"""
        for i, tax in enumerate(cls.DEFAULT_TAXES):
            tax_id = f"TAX-{i+1:03d}"
            cls._taxes[tax_id] = {
                "id": tax_id,
                **tax,
                "applies_to": ["products", "services"],
                "exempt_categories": [],
                "regions": [],
                "is_compound": False,
                "active": True,
                "created_at": utc_now().isoformat()
            }
        cls._counter = len(cls.DEFAULT_TAXES)

    def create_tax(
        self,
        name: str,
        code: str,
        tax_type: str,
        rate: float,
        applies_to: List[str] = None,
        exempt_categories: List[str] = None,
        regions: List[str] = None,
        is_compound: bool = False,
        is_default: bool = False
    ) -> dict:
        """Create a new tax rate"""
        self._counter += 1
        tax_id = f"TAX-{self._counter:03d}"

        # If setting as default, unset other defaults of same type
        if is_default:
            for t in self._taxes.values():
                if t["type"] == tax_type:
                    t["is_default"] = False

        tax = {
            "id": tax_id,
            "name": name,
            "code": code.upper(),
            "type": tax_type,
            "rate": rate,
            "applies_to": applies_to or ["products", "services"],
            "exempt_categories": exempt_categories or [],
            "regions": regions or [],
            "is_compound": is_compound,
            "is_default": is_default,
            "active": True,
            "created_at": utc_now().isoformat()
        }

        self._taxes[tax_id] = tax
        return tax

    def update_tax(self, tax_id: str, updates: dict) -> Optional[dict]:
        """Update a tax rate"""
        if tax_id not in self._taxes:
            return None

        tax = self._taxes[tax_id]

        for key, value in updates.items():
            if key in tax and key not in ["id", "created_at"]:
                tax[key] = value

        return tax

    def delete_tax(self, tax_id: str) -> bool:
        """Delete a tax rate"""
        if tax_id in self._taxes:
            del self._taxes[tax_id]
            return True
        return False

    def get_tax(self, tax_id: str) -> Optional[dict]:
        """Get a tax rate"""
        return self._taxes.get(tax_id)

    def get_by_code(self, code: str) -> Optional[dict]:
        """Get tax by code"""
        for tax in self._taxes.values():
            if tax["code"] == code.upper():
                return tax
        return None

    def list_taxes(self, active_only: bool = True, tax_type: str = None) -> List[dict]:
        """List all tax rates"""
        taxes = list(self._taxes.values())

        if active_only:
            taxes = [t for t in taxes if t["active"]]

        if tax_type:
            taxes = [t for t in taxes if t["type"] == tax_type]

        return sorted(taxes, key=lambda x: (x["type"], x["rate"]))

    def get_default_tax(self, tax_type: str = "vat") -> Optional[dict]:
        """Get default tax for a type"""
        for tax in self._taxes.values():
            if tax["type"] == tax_type and tax["is_default"] and tax["active"]:
                return tax
        return None

    def calculate_tax(
        self,
        amount: float,
        tax_id: str = None,
        tax_code: str = None,
        is_inclusive: bool = False
    ) -> dict:
        """Calculate tax for an amount"""
        tax = None

        if tax_id:
            tax = self.get_tax(tax_id)
        elif tax_code:
            tax = self.get_by_code(tax_code)
        else:
            tax = self.get_default_tax()

        if not tax:
            return {
                "amount": amount,
                "tax_amount": 0,
                "total": amount,
                "tax_rate": 0,
                "tax_id": None
            }

        rate = tax["rate"] / 100

        if is_inclusive:
            # Tax is already included in amount
            base = amount / (1 + rate)
            tax_amount = amount - base
        else:
            # Tax is on top of amount
            base = amount
            tax_amount = amount * rate

        # Round to 2 decimal places
        base = round(base, 2)
        tax_amount = round(tax_amount, 2)
        total = round(base + tax_amount, 2)

        return {
            "base_amount": base,
            "tax_amount": tax_amount,
            "total": total,
            "tax_rate": tax["rate"],
            "tax_id": tax["id"],
            "tax_code": tax["code"],
            "tax_name": tax["name"]
        }

    def calculate_multiple_taxes(
        self,
        amount: float,
        tax_ids: List[str],
        is_compound: bool = False
    ) -> dict:
        """Calculate multiple taxes"""
        results = []
        total_tax = 0
        running_amount = amount

        for tax_id in tax_ids:
            tax = self.get_tax(tax_id)
            if not tax:
                continue

            base = running_amount if is_compound else amount
            tax_amount = round(base * (tax["rate"] / 100), 2)
            total_tax += tax_amount

            results.append({
                "tax_id": tax_id,
                "tax_code": tax["code"],
                "tax_name": tax["name"],
                "tax_rate": tax["rate"],
                "tax_amount": tax_amount
            })

            if is_compound:
                running_amount += tax_amount

        return {
            "base_amount": amount,
            "taxes": results,
            "total_tax": round(total_tax, 2),
            "total": round(amount + total_tax, 2),
            "is_compound": is_compound
        }

    def generate_tax_report(
        self,
        period_start: str,
        period_end: str
    ) -> dict:
        """Generate tax report for a period"""
        transactions = db.transactions.find_all()

        # Filter by period
        period_txns = [
            t for t in transactions
            if period_start <= t.get("date", "") <= period_end
        ]

        # Calculate collected taxes (sales/income)
        collected = {}
        for txn in period_txns:
            if txn.get("type") == "income" and txn.get("tax_id"):
                tax_id = txn["tax_id"]
                tax_amount = txn.get("tax_amount", 0)
                if tax_id not in collected:
                    tax = self.get_tax(tax_id)
                    collected[tax_id] = {
                        "tax_code": tax["code"] if tax else "Unknown",
                        "tax_name": tax["name"] if tax else "Unknown",
                        "amount": 0,
                        "count": 0
                    }
                collected[tax_id]["amount"] += tax_amount
                collected[tax_id]["count"] += 1

        # Calculate paid taxes (purchases/expenses)
        paid = {}
        for txn in period_txns:
            if txn.get("type") == "expense" and txn.get("tax_id"):
                tax_id = txn["tax_id"]
                tax_amount = txn.get("tax_amount", 0)
                if tax_id not in paid:
                    tax = self.get_tax(tax_id)
                    paid[tax_id] = {
                        "tax_code": tax["code"] if tax else "Unknown",
                        "tax_name": tax["name"] if tax else "Unknown",
                        "amount": 0,
                        "count": 0
                    }
                paid[tax_id]["amount"] += tax_amount
                paid[tax_id]["count"] += 1

        total_collected = sum(c["amount"] for c in collected.values())
        total_paid = sum(p["amount"] for p in paid.values())

        return {
            "period_start": period_start,
            "period_end": period_end,
            "collected": list(collected.values()),
            "total_collected": round(total_collected, 2),
            "paid": list(paid.values()),
            "total_paid": round(total_paid, 2),
            "net_liability": round(total_collected - total_paid, 2),
            "transaction_count": len(period_txns)
        }


tax_service = TaxService()
