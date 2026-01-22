"""
Regional tax calculation module.
"""
from app.i18n.tax.core import TaxEngine, TaxResult, TaxType, TaxConfig
from app.i18n.tax.eu_vat import EUVATEngine, EU_VAT_RATES
from app.i18n.tax.us_sales import USSalesTaxEngine, US_STATE_RATES
from app.i18n.tax.validation import VATValidator, validate_vat_number

__all__ = [
    "TaxEngine",
    "TaxResult",
    "TaxType",
    "TaxConfig",
    "EUVATEngine",
    "EU_VAT_RATES",
    "USSalesTaxEngine",
    "US_STATE_RATES",
    "VATValidator",
    "validate_vat_number",
]
