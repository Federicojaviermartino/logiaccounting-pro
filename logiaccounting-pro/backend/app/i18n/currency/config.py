"""
Currency configuration and definitions.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class CurrencyPosition(str, Enum):
    """Currency symbol position."""
    BEFORE = "before"
    AFTER = "after"


@dataclass
class Currency:
    """Currency definition."""
    code: str
    name: str
    symbol: str
    decimal_places: int = 2
    symbol_position: CurrencyPosition = CurrencyPosition.BEFORE
    decimal_separator: str = "."
    thousands_separator: str = ","

    def format(self, amount: float) -> str:
        """Format amount in this currency."""
        from app.i18n.currency.formatter import CurrencyFormatter
        return CurrencyFormatter.format(amount, self)


class CurrencyConfig:
    """Currency configuration."""

    CURRENCIES: Dict[str, Currency] = {
        "USD": Currency(
            code="USD",
            name="US Dollar",
            symbol="$",
            decimal_places=2,
            symbol_position=CurrencyPosition.BEFORE,
        ),
        "EUR": Currency(
            code="EUR",
            name="Euro",
            symbol="€",
            decimal_places=2,
            symbol_position=CurrencyPosition.AFTER,
            decimal_separator=",",
            thousands_separator=".",
        ),
        "GBP": Currency(
            code="GBP",
            name="British Pound",
            symbol="£",
            decimal_places=2,
            symbol_position=CurrencyPosition.BEFORE,
        ),
        "JPY": Currency(
            code="JPY",
            name="Japanese Yen",
            symbol="¥",
            decimal_places=0,
            symbol_position=CurrencyPosition.BEFORE,
        ),
        "CHF": Currency(
            code="CHF",
            name="Swiss Franc",
            symbol="CHF",
            decimal_places=2,
            symbol_position=CurrencyPosition.BEFORE,
            decimal_separator=".",
            thousands_separator="'",
        ),
        "CAD": Currency(
            code="CAD",
            name="Canadian Dollar",
            symbol="$",
            decimal_places=2,
            symbol_position=CurrencyPosition.BEFORE,
        ),
        "AUD": Currency(
            code="AUD",
            name="Australian Dollar",
            symbol="$",
            decimal_places=2,
            symbol_position=CurrencyPosition.BEFORE,
        ),
        "CNY": Currency(
            code="CNY",
            name="Chinese Yuan",
            symbol="¥",
            decimal_places=2,
            symbol_position=CurrencyPosition.BEFORE,
        ),
        "INR": Currency(
            code="INR",
            name="Indian Rupee",
            symbol="₹",
            decimal_places=2,
            symbol_position=CurrencyPosition.BEFORE,
        ),
        "MXN": Currency(
            code="MXN",
            name="Mexican Peso",
            symbol="$",
            decimal_places=2,
            symbol_position=CurrencyPosition.BEFORE,
        ),
        "BRL": Currency(
            code="BRL",
            name="Brazilian Real",
            symbol="R$",
            decimal_places=2,
            symbol_position=CurrencyPosition.BEFORE,
            decimal_separator=",",
            thousands_separator=".",
        ),
        "ARS": Currency(
            code="ARS",
            name="Argentine Peso",
            symbol="$",
            decimal_places=2,
            symbol_position=CurrencyPosition.BEFORE,
            decimal_separator=",",
            thousands_separator=".",
        ),
        "CLP": Currency(
            code="CLP",
            name="Chilean Peso",
            symbol="$",
            decimal_places=0,
            symbol_position=CurrencyPosition.BEFORE,
            decimal_separator=",",
            thousands_separator=".",
        ),
        "COP": Currency(
            code="COP",
            name="Colombian Peso",
            symbol="$",
            decimal_places=2,
            symbol_position=CurrencyPosition.BEFORE,
            decimal_separator=",",
            thousands_separator=".",
        ),
        "PEN": Currency(
            code="PEN",
            name="Peruvian Sol",
            symbol="S/",
            decimal_places=2,
            symbol_position=CurrencyPosition.BEFORE,
        ),
        "PLN": Currency(
            code="PLN",
            name="Polish Zloty",
            symbol="zł",
            decimal_places=2,
            symbol_position=CurrencyPosition.AFTER,
            decimal_separator=",",
            thousands_separator=" ",
        ),
        "SEK": Currency(
            code="SEK",
            name="Swedish Krona",
            symbol="kr",
            decimal_places=2,
            symbol_position=CurrencyPosition.AFTER,
            decimal_separator=",",
            thousands_separator=" ",
        ),
        "NOK": Currency(
            code="NOK",
            name="Norwegian Krone",
            symbol="kr",
            decimal_places=2,
            symbol_position=CurrencyPosition.AFTER,
            decimal_separator=",",
            thousands_separator=" ",
        ),
        "DKK": Currency(
            code="DKK",
            name="Danish Krone",
            symbol="kr",
            decimal_places=2,
            symbol_position=CurrencyPosition.AFTER,
            decimal_separator=",",
            thousands_separator=".",
        ),
        "RUB": Currency(
            code="RUB",
            name="Russian Ruble",
            symbol="₽",
            decimal_places=2,
            symbol_position=CurrencyPosition.AFTER,
            decimal_separator=",",
            thousands_separator=" ",
        ),
        "SAR": Currency(
            code="SAR",
            name="Saudi Riyal",
            symbol="﷼",
            decimal_places=2,
            symbol_position=CurrencyPosition.AFTER,
        ),
        "AED": Currency(
            code="AED",
            name="UAE Dirham",
            symbol="د.إ",
            decimal_places=2,
            symbol_position=CurrencyPosition.AFTER,
        ),
        "KRW": Currency(
            code="KRW",
            name="South Korean Won",
            symbol="₩",
            decimal_places=0,
            symbol_position=CurrencyPosition.BEFORE,
        ),
        "SGD": Currency(
            code="SGD",
            name="Singapore Dollar",
            symbol="$",
            decimal_places=2,
            symbol_position=CurrencyPosition.BEFORE,
        ),
    }

    BASE_CURRENCY = "USD"

    @classmethod
    def get_currency(cls, code: str) -> Optional[Currency]:
        """Get currency by code."""
        return cls.CURRENCIES.get(code.upper())

    @classmethod
    def get_all_currencies(cls) -> List[Currency]:
        """Get all supported currencies."""
        return list(cls.CURRENCIES.values())

    @classmethod
    def get_currency_codes(cls) -> List[str]:
        """Get all currency codes."""
        return list(cls.CURRENCIES.keys())

    @classmethod
    def is_supported(cls, code: str) -> bool:
        """Check if currency is supported."""
        return code.upper() in cls.CURRENCIES
