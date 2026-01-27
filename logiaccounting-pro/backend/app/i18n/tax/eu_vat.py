"""
EU VAT calculation engine.
"""
from dataclasses import dataclass
from typing import Dict, Optional

from app.i18n.tax.core import TaxEngine, TaxResult, TaxType


@dataclass
class VATRate:
    """VAT rate configuration."""
    country_code: str
    country_name: str
    standard_rate: float
    reduced_rate: float = 0.0
    reduced_rate_2: float = 0.0
    super_reduced_rate: float = 0.0
    parking_rate: float = 0.0


EU_VAT_RATES: Dict[str, VATRate] = {
    "AT": VATRate("AT", "Austria", 20.0, 10.0, 13.0),
    "BE": VATRate("BE", "Belgium", 21.0, 6.0, 12.0),
    "BG": VATRate("BG", "Bulgaria", 20.0, 9.0),
    "HR": VATRate("HR", "Croatia", 25.0, 5.0, 13.0),
    "CY": VATRate("CY", "Cyprus", 19.0, 5.0, 9.0),
    "CZ": VATRate("CZ", "Czech Republic", 21.0, 10.0, 15.0),
    "DK": VATRate("DK", "Denmark", 25.0),
    "EE": VATRate("EE", "Estonia", 22.0, 9.0),
    "FI": VATRate("FI", "Finland", 24.0, 10.0, 14.0),
    "FR": VATRate("FR", "France", 20.0, 5.5, 10.0, 2.1),
    "DE": VATRate("DE", "Germany", 19.0, 7.0),
    "GR": VATRate("GR", "Greece", 24.0, 6.0, 13.0),
    "HU": VATRate("HU", "Hungary", 27.0, 5.0, 18.0),
    "IE": VATRate("IE", "Ireland", 23.0, 9.0, 13.5, 4.8, 13.5),
    "IT": VATRate("IT", "Italy", 22.0, 4.0, 10.0),
    "LV": VATRate("LV", "Latvia", 21.0, 12.0, 5.0),
    "LT": VATRate("LT", "Lithuania", 21.0, 5.0, 9.0),
    "LU": VATRate("LU", "Luxembourg", 17.0, 3.0, 8.0, 0.0, 14.0),
    "MT": VATRate("MT", "Malta", 18.0, 5.0, 7.0),
    "NL": VATRate("NL", "Netherlands", 21.0, 9.0),
    "PL": VATRate("PL", "Poland", 23.0, 5.0, 8.0),
    "PT": VATRate("PT", "Portugal", 23.0, 6.0, 13.0),
    "RO": VATRate("RO", "Romania", 19.0, 5.0, 9.0),
    "SK": VATRate("SK", "Slovakia", 20.0, 10.0),
    "SI": VATRate("SI", "Slovenia", 22.0, 5.0, 9.5),
    "ES": VATRate("ES", "Spain", 21.0, 4.0, 10.0),
    "SE": VATRate("SE", "Sweden", 25.0, 6.0, 12.0),
    "GB": VATRate("GB", "United Kingdom", 20.0, 5.0),
}

REDUCED_RATE_CATEGORIES = {
    "food": "reduced",
    "books": "reduced",
    "newspapers": "reduced",
    "pharmaceuticals": "reduced",
    "medical_equipment": "reduced",
    "passenger_transport": "reduced",
    "hotels": "reduced_2",
    "restaurants": "reduced_2",
    "cultural_events": "reduced",
    "children_clothing": "super_reduced",
    "children_shoes": "super_reduced",
}


class EUVATEngine(TaxEngine):
    """EU VAT calculation engine."""

    def __init__(self, country_code: str):
        self.country_code = country_code.upper()
        self.vat_config = EU_VAT_RATES.get(self.country_code)
        if not self.vat_config:
            raise ValueError(f"Unsupported EU country: {country_code}")

    @property
    def tax_type(self) -> TaxType:
        return TaxType.VAT

    @property
    def region(self) -> str:
        return self.country_code

    def get_rate(
        self,
        category: Optional[str] = None,
        rate_type: Optional[str] = None,
        **kwargs
    ) -> float:
        """
        Get VAT rate.

        Args:
            category: Product category
            rate_type: Explicit rate type (standard, reduced, reduced_2, super_reduced)
        """
        if rate_type == "reduced" and self.vat_config.reduced_rate:
            return self.vat_config.reduced_rate
        elif rate_type == "reduced_2" and self.vat_config.reduced_rate_2:
            return self.vat_config.reduced_rate_2
        elif rate_type == "super_reduced" and self.vat_config.super_reduced_rate:
            return self.vat_config.super_reduced_rate
        elif rate_type == "parking" and self.vat_config.parking_rate:
            return self.vat_config.parking_rate

        if category:
            category_rate_type = REDUCED_RATE_CATEGORIES.get(category.lower())
            if category_rate_type == "reduced" and self.vat_config.reduced_rate:
                return self.vat_config.reduced_rate
            elif category_rate_type == "reduced_2" and self.vat_config.reduced_rate_2:
                return self.vat_config.reduced_rate_2
            elif category_rate_type == "super_reduced" and self.vat_config.super_reduced_rate:
                return self.vat_config.super_reduced_rate

        return self.vat_config.standard_rate

    def calculate(
        self,
        amount: float,
        category: Optional[str] = None,
        is_tax_included: bool = False,
        is_reverse_charge: bool = False,
        buyer_vat_number: Optional[str] = None,
        buyer_country: Optional[str] = None,
        **kwargs
    ) -> TaxResult:
        """
        Calculate EU VAT.

        Args:
            amount: Amount to calculate VAT for
            category: Product/service category
            is_tax_included: Whether amount includes VAT
            is_reverse_charge: Whether reverse charge applies
            buyer_vat_number: Buyer's VAT number (for B2B transactions)
            buyer_country: Buyer's country code
        """
        is_b2b_cross_border = (
            buyer_vat_number
            and buyer_country
            and buyer_country.upper() != self.country_code
        )

        if is_reverse_charge or is_b2b_cross_border:
            return TaxResult(
                gross_amount=amount,
                net_amount=amount,
                tax_amount=0.0,
                tax_rate=0.0,
                tax_type=self.tax_type,
                region=self.region,
                is_exempt=True,
                exempt_reason="Reverse charge" if is_reverse_charge else "B2B intra-EU supply",
            )

        rate = self.get_rate(category, **kwargs)

        if is_tax_included:
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
            breakdown={
                "vat": tax,
                "rate_type": self._get_rate_type(rate),
            },
        )

    def _get_rate_type(self, rate: float) -> str:
        """Determine rate type from rate value."""
        if rate == self.vat_config.standard_rate:
            return "standard"
        elif rate == self.vat_config.reduced_rate:
            return "reduced"
        elif rate == self.vat_config.reduced_rate_2:
            return "reduced_2"
        elif rate == self.vat_config.super_reduced_rate:
            return "super_reduced"
        elif rate == self.vat_config.parking_rate:
            return "parking"
        return "custom"

    @classmethod
    def get_all_rates(cls) -> Dict[str, VATRate]:
        """Get all EU VAT rates."""
        return EU_VAT_RATES

    @classmethod
    def is_eu_country(cls, country_code: str) -> bool:
        """Check if country is in EU."""
        return country_code.upper() in EU_VAT_RATES
