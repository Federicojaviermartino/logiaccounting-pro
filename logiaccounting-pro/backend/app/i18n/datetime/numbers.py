"""
Number formatting utilities.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union

from app.i18n.core.context import get_locale
from app.i18n.core.locale import LocaleContext


class NumberFormatter:
    """Number formatting utilities."""

    @classmethod
    def format(
        cls,
        value: Union[int, float, Decimal, str],
        decimal_places: Optional[int] = None,
        locale: Optional[LocaleContext] = None,
        use_grouping: bool = True
    ) -> str:
        """
        Format number according to locale.

        Args:
            value: Number to format
            decimal_places: Number of decimal places (auto if None)
            locale: Locale context
            use_grouping: Whether to use thousands grouping
        """
        if not locale:
            locale = get_locale()

        try:
            num = Decimal(str(value))
        except Exception:
            return str(value)

        if decimal_places is None:
            str_val = str(num)
            if "." in str_val:
                decimal_places = min(len(str_val.split(".")[1]), locale.number_format.decimal_places)
            else:
                decimal_places = 0

        if decimal_places > 0:
            quantized = num.quantize(
                Decimal(10) ** -decimal_places,
                rounding=ROUND_HALF_UP
            )
        else:
            quantized = num.quantize(Decimal(1), rounding=ROUND_HALF_UP)

        is_negative = quantized < 0
        abs_val = abs(quantized)

        if decimal_places > 0:
            str_val = f"{abs_val:.{decimal_places}f}"
        else:
            str_val = str(int(abs_val))

        if "." in str_val:
            integer_part, decimal_part = str_val.split(".")
        else:
            integer_part = str_val
            decimal_part = ""

        if use_grouping:
            formatted_integer = ""
            for i, digit in enumerate(reversed(integer_part)):
                if i > 0 and i % 3 == 0:
                    formatted_integer = locale.number_format.thousands_separator + formatted_integer
                formatted_integer = digit + formatted_integer
        else:
            formatted_integer = integer_part

        if decimal_part:
            result = f"{formatted_integer}{locale.number_format.decimal_separator}{decimal_part}"
        else:
            result = formatted_integer

        if is_negative:
            result = f"-{result}"

        return result

    @classmethod
    def format_decimal(
        cls,
        value: Union[int, float, Decimal, str],
        decimal_places: int = 2,
        locale: Optional[LocaleContext] = None
    ) -> str:
        """Format as decimal with fixed places."""
        return cls.format(value, decimal_places, locale)

    @classmethod
    def format_integer(
        cls,
        value: Union[int, float, Decimal, str],
        locale: Optional[LocaleContext] = None
    ) -> str:
        """Format as integer."""
        return cls.format(value, 0, locale)

    @classmethod
    def format_percent(
        cls,
        value: Union[int, float, Decimal, str],
        decimal_places: int = 1,
        locale: Optional[LocaleContext] = None,
        multiply: bool = False
    ) -> str:
        """
        Format as percentage.

        Args:
            value: Value to format
            decimal_places: Decimal places
            locale: Locale context
            multiply: If True, multiply by 100 (e.g., 0.5 -> 50%)
        """
        if not locale:
            locale = get_locale()

        try:
            num = Decimal(str(value))
            if multiply:
                num = num * 100
        except Exception:
            return str(value)

        formatted = cls.format(num, decimal_places, locale, use_grouping=False)
        return f"{formatted}%"

    @classmethod
    def format_compact(
        cls,
        value: Union[int, float, Decimal, str],
        locale: Optional[LocaleContext] = None
    ) -> str:
        """
        Format large numbers in compact form (e.g., 1.5K, 2.3M).

        Args:
            value: Number to format
            locale: Locale context
        """
        if not locale:
            locale = get_locale()

        try:
            num = float(value)
        except Exception:
            return str(value)

        abs_num = abs(num)
        sign = "-" if num < 0 else ""

        if abs_num >= 1_000_000_000_000:
            compact = abs_num / 1_000_000_000_000
            suffix = "T"
        elif abs_num >= 1_000_000_000:
            compact = abs_num / 1_000_000_000
            suffix = "B"
        elif abs_num >= 1_000_000:
            compact = abs_num / 1_000_000
            suffix = "M"
        elif abs_num >= 1_000:
            compact = abs_num / 1_000
            suffix = "K"
        else:
            return cls.format(num, locale=locale)

        if compact >= 100:
            formatted = cls.format(compact, 0, locale, use_grouping=False)
        elif compact >= 10:
            formatted = cls.format(compact, 1, locale, use_grouping=False)
        else:
            formatted = cls.format(compact, 2, locale, use_grouping=False)

        return f"{sign}{formatted}{suffix}"

    @classmethod
    def parse(
        cls,
        value: str,
        locale: Optional[LocaleContext] = None
    ) -> Optional[Decimal]:
        """
        Parse formatted number string.

        Args:
            value: Formatted number string
            locale: Locale context

        Returns:
            Decimal or None if parse failed
        """
        if not locale:
            locale = get_locale()

        if not value:
            return None

        cleaned = value.strip()

        is_negative = False
        if cleaned.startswith("-"):
            is_negative = True
            cleaned = cleaned[1:]
        elif cleaned.startswith("(") and cleaned.endswith(")"):
            is_negative = True
            cleaned = cleaned[1:-1]

        if cleaned.endswith("%"):
            cleaned = cleaned[:-1]

        cleaned = cleaned.replace(locale.number_format.thousands_separator, "")
        cleaned = cleaned.replace(locale.number_format.decimal_separator, ".")

        try:
            result = Decimal(cleaned)
            return -result if is_negative else result
        except Exception:
            return None


def format_number(
    value: Union[int, float, Decimal, str],
    decimal_places: Optional[int] = None
) -> str:
    """Shorthand for number formatting."""
    return NumberFormatter.format(value, decimal_places)


def format_decimal(
    value: Union[int, float, Decimal, str],
    decimal_places: int = 2
) -> str:
    """Shorthand for decimal formatting."""
    return NumberFormatter.format_decimal(value, decimal_places)


def format_percent(
    value: Union[int, float, Decimal, str],
    decimal_places: int = 1
) -> str:
    """Shorthand for percent formatting."""
    return NumberFormatter.format_percent(value, decimal_places)


def parse_number(value: str) -> Optional[Decimal]:
    """Shorthand for number parsing."""
    return NumberFormatter.parse(value)
