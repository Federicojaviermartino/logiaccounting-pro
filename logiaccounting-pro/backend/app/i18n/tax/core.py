"""
Core tax calculation engine.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Dict, List, Optional


class TaxType(str, Enum):
    """Tax types."""
    VAT = "vat"
    SALES_TAX = "sales_tax"
    GST = "gst"
    HST = "hst"
    PST = "pst"
    EXEMPT = "exempt"


@dataclass
class TaxConfig:
    """Tax configuration for a region."""
    region: str
    tax_type: TaxType
    standard_rate: float
    reduced_rates: Dict[str, float] = field(default_factory=dict)
    exempt_categories: List[str] = field(default_factory=list)
    tax_included_default: bool = False
    name: str = ""

    def __post_init__(self):
        if not self.name:
            self.name = f"{self.region} {self.tax_type.value.upper()}"


@dataclass
class TaxResult:
    """Tax calculation result."""
    gross_amount: float
    net_amount: float
    tax_amount: float
    tax_rate: float
    tax_type: TaxType
    region: str
    breakdown: Dict[str, float] = field(default_factory=dict)
    is_exempt: bool = False
    exempt_reason: Optional[str] = None

    @property
    def effective_rate(self) -> float:
        """Calculate effective tax rate."""
        if self.net_amount == 0:
            return 0.0
        return (self.tax_amount / self.net_amount) * 100


class TaxEngine(ABC):
    """Base tax calculation engine."""

    @property
    @abstractmethod
    def tax_type(self) -> TaxType:
        """Get tax type."""
        pass

    @property
    @abstractmethod
    def region(self) -> str:
        """Get region code."""
        pass

    @abstractmethod
    def calculate(
        self,
        amount: float,
        category: Optional[str] = None,
        is_tax_included: bool = False,
        **kwargs
    ) -> TaxResult:
        """
        Calculate tax for an amount.

        Args:
            amount: Amount to calculate tax for
            category: Product/service category for rate determination
            is_tax_included: Whether amount includes tax
            **kwargs: Additional parameters for specific tax types

        Returns:
            TaxResult with calculation details
        """
        pass

    @abstractmethod
    def get_rate(
        self,
        category: Optional[str] = None,
        **kwargs
    ) -> float:
        """Get applicable tax rate."""
        pass

    def calculate_net_from_gross(
        self,
        gross_amount: float,
        tax_rate: float
    ) -> tuple:
        """Calculate net amount and tax from gross (tax-inclusive amount)."""
        gross = Decimal(str(gross_amount))
        rate = Decimal(str(tax_rate)) / 100

        net = gross / (1 + rate)
        tax = gross - net

        net = float(net.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        tax = float(tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        return net, tax

    def calculate_gross_from_net(
        self,
        net_amount: float,
        tax_rate: float
    ) -> tuple:
        """Calculate gross amount and tax from net (tax-exclusive amount)."""
        net = Decimal(str(net_amount))
        rate = Decimal(str(tax_rate)) / 100

        tax = net * rate
        gross = net + tax

        tax = float(tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        gross = float(gross.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        return gross, tax


class SimpleTaxEngine(TaxEngine):
    """Simple single-rate tax engine."""

    def __init__(self, config: TaxConfig):
        self.config = config

    @property
    def tax_type(self) -> TaxType:
        return self.config.tax_type

    @property
    def region(self) -> str:
        return self.config.region

    def get_rate(
        self,
        category: Optional[str] = None,
        **kwargs
    ) -> float:
        """Get applicable rate."""
        if category and category in self.config.exempt_categories:
            return 0.0

        if category and category in self.config.reduced_rates:
            return self.config.reduced_rates[category]

        return self.config.standard_rate

    def calculate(
        self,
        amount: float,
        category: Optional[str] = None,
        is_tax_included: bool = False,
        **kwargs
    ) -> TaxResult:
        """Calculate tax."""
        rate = self.get_rate(category)
        is_exempt = rate == 0.0

        if is_tax_included or self.config.tax_included_default:
            net, tax = self.calculate_net_from_gross(amount, rate)
            gross = amount
        else:
            gross, tax = self.calculate_gross_from_net(amount, rate)
            net = amount

        return TaxResult(
            gross_amount=gross,
            net_amount=net,
            tax_amount=tax,
            tax_rate=rate,
            tax_type=self.tax_type,
            region=self.region,
            is_exempt=is_exempt,
            exempt_reason="Exempt category" if is_exempt and category else None,
        )
