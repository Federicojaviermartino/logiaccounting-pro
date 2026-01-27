"""
Currency formatting utilities.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.i18n.currency.config import Currency, CurrencyConfig, CurrencyPosition
from app.i18n.core.context import get_locale


class CurrencyFormatter:
    """Currency formatting operations."""

    @classmethod
    def format(
        cls,
        amount: float,
        currency: Optional[Currency] = None,
        currency_code: Optional[str] = None,
        show_symbol: bool = True,
        show_code: bool = False,
        decimal_places: Optional[int] = None
    ) -> str:
        """
        Format amount as currency.

        Args:
            amount: Amount to format
            currency: Currency object
            currency_code: Currency code (used if currency not provided)
            show_symbol: Whether to show currency symbol
            show_code: Whether to show currency code
            decimal_places: Override decimal places

        Returns:
            Formatted currency string
        """
        if not currency and currency_code:
            currency = CurrencyConfig.get_currency(currency_code)

        if not currency:
            locale = get_locale()
            currency = CurrencyConfig.get_currency(locale.currency)

        if not currency:
            currency = CurrencyConfig.get_currency("USD")

        places = decimal_places if decimal_places is not None else currency.decimal_places

        formatted_number = cls._format_number(
            amount,
            places,
            currency.decimal_separator,
            currency.thousands_separator
        )

        if show_symbol:
            if currency.symbol_position == CurrencyPosition.BEFORE:
                result = f"{currency.symbol}{formatted_number}"
            else:
                result = f"{formatted_number} {currency.symbol}"
        else:
            result = formatted_number

        if show_code:
            result = f"{result} {currency.code}"

        return result

    @classmethod
    def _format_number(
        cls,
        amount: float,
        decimal_places: int,
        decimal_separator: str,
        thousands_separator: str
    ) -> str:
        """Format number with proper separators."""
        decimal_amount = Decimal(str(amount))
        if decimal_places > 0:
            quantized = decimal_amount.quantize(
                Decimal(10) ** -decimal_places,
                rounding=ROUND_HALF_UP
            )
        else:
            quantized = decimal_amount.quantize(Decimal(1), rounding=ROUND_HALF_UP)

        is_negative = quantized < 0
        abs_amount = abs(quantized)

        if decimal_places > 0:
            str_amount = f"{abs_amount:.{decimal_places}f}"
        else:
            str_amount = str(int(abs_amount))

        if "." in str_amount:
            integer_part, decimal_part = str_amount.split(".")
        else:
            integer_part = str_amount
            decimal_part = ""

        formatted_integer = ""
        for i, digit in enumerate(reversed(integer_part)):
            if i > 0 and i % 3 == 0:
                formatted_integer = thousands_separator + formatted_integer
            formatted_integer = digit + formatted_integer

        if decimal_part:
            result = f"{formatted_integer}{decimal_separator}{decimal_part}"
        else:
            result = formatted_integer

        if is_negative:
            result = f"-{result}"

        return result

    @classmethod
    def format_accounting(
        cls,
        amount: float,
        currency: Optional[Currency] = None,
        currency_code: Optional[str] = None
    ) -> str:
        """
        Format amount in accounting format (negative in parentheses).

        Args:
            amount: Amount to format
            currency: Currency object
            currency_code: Currency code

        Returns:
            Formatted string with negatives in parentheses
        """
        if not currency and currency_code:
            currency = CurrencyConfig.get_currency(currency_code)

        if not currency:
            locale = get_locale()
            currency = CurrencyConfig.get_currency(locale.currency)

        if not currency:
            currency = CurrencyConfig.get_currency("USD")

        is_negative = amount < 0
        formatted = cls.format(abs(amount), currency)

        if is_negative:
            return f"({formatted})"
        return formatted

    @classmethod
    def parse(
        cls,
        value: str,
        currency_code: Optional[str] = None
    ) -> Optional[float]:
        """
        Parse currency string to float.

        Args:
            value: Currency string to parse
            currency_code: Expected currency code

        Returns:
            Parsed amount or None
        """
        if not value:
            return None

        currency = None
        if currency_code:
            currency = CurrencyConfig.get_currency(currency_code)

        cleaned = value.strip()

        for curr in CurrencyConfig.CURRENCIES.values():
            cleaned = cleaned.replace(curr.symbol, "")
            cleaned = cleaned.replace(curr.code, "")

        cleaned = cleaned.strip()

        is_negative = False
        if cleaned.startswith("(") and cleaned.endswith(")"):
            is_negative = True
            cleaned = cleaned[1:-1]
        elif cleaned.startswith("-"):
            is_negative = True
            cleaned = cleaned[1:]

        if currency:
            cleaned = cleaned.replace(currency.thousands_separator, "")
            cleaned = cleaned.replace(currency.decimal_separator, ".")
        else:
            for sep in [" ", "'", ".", ","]:
                if sep in cleaned:
                    parts = cleaned.split(sep)
                    if len(parts[-1]) == 2:
                        cleaned = "".join(parts[:-1]) + "." + parts[-1]
                    else:
                        cleaned = "".join(parts)
                    break

        try:
            amount = float(cleaned)
            return -amount if is_negative else amount
        except ValueError:
            return None


def format_currency(
    amount: float,
    currency_code: Optional[str] = None,
    show_symbol: bool = True
) -> str:
    """Shorthand for currency formatting."""
    return CurrencyFormatter.format(
        amount,
        currency_code=currency_code,
        show_symbol=show_symbol
    )
