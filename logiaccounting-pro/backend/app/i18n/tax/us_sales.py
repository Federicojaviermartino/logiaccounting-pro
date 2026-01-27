"""
US Sales Tax calculation engine.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional

from app.i18n.tax.core import TaxEngine, TaxResult, TaxType


@dataclass
class StateTaxRate:
    """State sales tax rate configuration."""
    state_code: str
    state_name: str
    state_rate: float
    has_local_tax: bool = True
    max_local_rate: float = 0.0
    exempt_food: bool = False
    exempt_clothing: bool = False
    exempt_medicine: bool = True


US_STATE_RATES: Dict[str, StateTaxRate] = {
    "AL": StateTaxRate("AL", "Alabama", 4.0, True, 7.5),
    "AK": StateTaxRate("AK", "Alaska", 0.0, True, 7.5),
    "AZ": StateTaxRate("AZ", "Arizona", 5.6, True, 5.6),
    "AR": StateTaxRate("AR", "Arkansas", 6.5, True, 5.125, exempt_food=True),
    "CA": StateTaxRate("CA", "California", 7.25, True, 2.5),
    "CO": StateTaxRate("CO", "Colorado", 2.9, True, 8.3),
    "CT": StateTaxRate("CT", "Connecticut", 6.35, False, 0.0, exempt_clothing=True),
    "DE": StateTaxRate("DE", "Delaware", 0.0, False, 0.0),
    "FL": StateTaxRate("FL", "Florida", 6.0, True, 2.0),
    "GA": StateTaxRate("GA", "Georgia", 4.0, True, 4.9),
    "HI": StateTaxRate("HI", "Hawaii", 4.0, True, 0.5),
    "ID": StateTaxRate("ID", "Idaho", 6.0, True, 3.0),
    "IL": StateTaxRate("IL", "Illinois", 6.25, True, 4.75),
    "IN": StateTaxRate("IN", "Indiana", 7.0, False, 0.0),
    "IA": StateTaxRate("IA", "Iowa", 6.0, True, 1.0),
    "KS": StateTaxRate("KS", "Kansas", 6.5, True, 4.0),
    "KY": StateTaxRate("KY", "Kentucky", 6.0, False, 0.0),
    "LA": StateTaxRate("LA", "Louisiana", 4.45, True, 7.0),
    "ME": StateTaxRate("ME", "Maine", 5.5, False, 0.0),
    "MD": StateTaxRate("MD", "Maryland", 6.0, False, 0.0),
    "MA": StateTaxRate("MA", "Massachusetts", 6.25, False, 0.0, exempt_clothing=True),
    "MI": StateTaxRate("MI", "Michigan", 6.0, False, 0.0),
    "MN": StateTaxRate("MN", "Minnesota", 6.875, True, 2.0, exempt_clothing=True),
    "MS": StateTaxRate("MS", "Mississippi", 7.0, True, 1.0),
    "MO": StateTaxRate("MO", "Missouri", 4.225, True, 5.763),
    "MT": StateTaxRate("MT", "Montana", 0.0, False, 0.0),
    "NE": StateTaxRate("NE", "Nebraska", 5.5, True, 2.0),
    "NV": StateTaxRate("NV", "Nevada", 6.85, True, 1.53),
    "NH": StateTaxRate("NH", "New Hampshire", 0.0, False, 0.0),
    "NJ": StateTaxRate("NJ", "New Jersey", 6.625, False, 0.0, exempt_clothing=True),
    "NM": StateTaxRate("NM", "New Mexico", 4.875, True, 4.313),
    "NY": StateTaxRate("NY", "New York", 4.0, True, 4.875, exempt_clothing=True),
    "NC": StateTaxRate("NC", "North Carolina", 4.75, True, 2.75),
    "ND": StateTaxRate("ND", "North Dakota", 5.0, True, 3.0),
    "OH": StateTaxRate("OH", "Ohio", 5.75, True, 2.25),
    "OK": StateTaxRate("OK", "Oklahoma", 4.5, True, 7.0),
    "OR": StateTaxRate("OR", "Oregon", 0.0, False, 0.0),
    "PA": StateTaxRate("PA", "Pennsylvania", 6.0, True, 2.0, exempt_clothing=True),
    "RI": StateTaxRate("RI", "Rhode Island", 7.0, False, 0.0, exempt_clothing=True),
    "SC": StateTaxRate("SC", "South Carolina", 6.0, True, 3.0),
    "SD": StateTaxRate("SD", "South Dakota", 4.2, True, 4.5),
    "TN": StateTaxRate("TN", "Tennessee", 7.0, True, 2.75),
    "TX": StateTaxRate("TX", "Texas", 6.25, True, 2.0),
    "UT": StateTaxRate("UT", "Utah", 6.1, True, 2.95),
    "VT": StateTaxRate("VT", "Vermont", 6.0, True, 1.0, exempt_clothing=True),
    "VA": StateTaxRate("VA", "Virginia", 5.3, True, 0.7),
    "WA": StateTaxRate("WA", "Washington", 6.5, True, 4.0),
    "WV": StateTaxRate("WV", "West Virginia", 6.0, True, 1.0),
    "WI": StateTaxRate("WI", "Wisconsin", 5.0, True, 1.75),
    "WY": StateTaxRate("WY", "Wyoming", 4.0, True, 2.0),
    "DC": StateTaxRate("DC", "District of Columbia", 6.0, False, 0.0),
}

NO_SALES_TAX_STATES = {"DE", "MT", "NH", "OR", "AK"}

EXEMPT_CATEGORIES = {
    "groceries": "food",
    "food": "food",
    "clothing": "clothing",
    "apparel": "clothing",
    "medicine": "medicine",
    "prescription": "medicine",
    "medical": "medicine",
}


class USSalesTaxEngine(TaxEngine):
    """US Sales Tax calculation engine."""

    def __init__(self, state_code: str, local_rate: float = 0.0):
        """
        Initialize US Sales Tax engine.

        Args:
            state_code: Two-letter state code
            local_rate: Local (city/county) tax rate
        """
        self.state_code = state_code.upper()
        self.local_rate = local_rate
        self.state_config = US_STATE_RATES.get(self.state_code)
        if not self.state_config:
            raise ValueError(f"Unsupported US state: {state_code}")

    @property
    def tax_type(self) -> TaxType:
        return TaxType.SALES_TAX

    @property
    def region(self) -> str:
        return f"US-{self.state_code}"

    def get_rate(
        self,
        category: Optional[str] = None,
        include_local: bool = True,
        **kwargs
    ) -> float:
        """
        Get applicable sales tax rate.

        Args:
            category: Product category for exemption check
            include_local: Whether to include local tax
        """
        if category:
            exempt_type = EXEMPT_CATEGORIES.get(category.lower())
            if exempt_type == "food" and self.state_config.exempt_food:
                return 0.0
            elif exempt_type == "clothing" and self.state_config.exempt_clothing:
                return 0.0
            elif exempt_type == "medicine" and self.state_config.exempt_medicine:
                return 0.0

        state_rate = self.state_config.state_rate
        local = self.local_rate if include_local else 0.0

        return state_rate + local

    def calculate(
        self,
        amount: float,
        category: Optional[str] = None,
        is_tax_included: bool = False,
        include_local: bool = True,
        is_resale: bool = False,
        **kwargs
    ) -> TaxResult:
        """
        Calculate US Sales Tax.

        Args:
            amount: Amount to calculate tax for
            category: Product category
            is_tax_included: Whether amount includes tax
            include_local: Whether to include local tax
            is_resale: Whether this is a resale (exempt with certificate)
        """
        if is_resale:
            return TaxResult(
                gross_amount=amount,
                net_amount=amount,
                tax_amount=0.0,
                tax_rate=0.0,
                tax_type=self.tax_type,
                region=self.region,
                is_exempt=True,
                exempt_reason="Resale exemption",
            )

        rate = self.get_rate(category, include_local)

        if rate == 0.0:
            exempt_type = EXEMPT_CATEGORIES.get(category.lower()) if category else None
            return TaxResult(
                gross_amount=amount,
                net_amount=amount,
                tax_amount=0.0,
                tax_rate=0.0,
                tax_type=self.tax_type,
                region=self.region,
                is_exempt=True,
                exempt_reason=f"Exempt category: {exempt_type}" if exempt_type else "No sales tax",
            )

        if is_tax_included:
            net, tax = self.calculate_net_from_gross(amount, rate)
            gross = amount
        else:
            gross, tax = self.calculate_gross_from_net(amount, rate)
            net = amount

        state_portion = self._calculate_portion(
            tax, self.state_config.state_rate, rate
        )
        local_portion = self._calculate_portion(
            tax, self.local_rate, rate
        )

        return TaxResult(
            gross_amount=gross,
            net_amount=net,
            tax_amount=tax,
            tax_rate=rate,
            tax_type=self.tax_type,
            region=self.region,
            breakdown={
                "state_tax": state_portion,
                "local_tax": local_portion,
                "state_rate": self.state_config.state_rate,
                "local_rate": self.local_rate,
            },
        )

    def _calculate_portion(
        self,
        total_tax: float,
        portion_rate: float,
        total_rate: float
    ) -> float:
        """Calculate tax portion for a specific rate."""
        if total_rate == 0:
            return 0.0
        portion = Decimal(str(total_tax)) * Decimal(str(portion_rate)) / Decimal(str(total_rate))
        return float(portion.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    @classmethod
    def get_state_rate(cls, state_code: str) -> Optional[float]:
        """Get state sales tax rate."""
        config = US_STATE_RATES.get(state_code.upper())
        return config.state_rate if config else None

    @classmethod
    def get_no_tax_states(cls) -> List[str]:
        """Get states with no sales tax."""
        return list(NO_SALES_TAX_STATES)

    @classmethod
    def has_sales_tax(cls, state_code: str) -> bool:
        """Check if state has sales tax."""
        return state_code.upper() not in NO_SALES_TAX_STATES
