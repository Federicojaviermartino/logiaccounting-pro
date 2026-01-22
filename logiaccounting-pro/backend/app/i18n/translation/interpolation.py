"""
Variable interpolation for translations.
"""
import re
from typing import Any, Dict
import html


def interpolate(
    message: str,
    variables: Dict[str, Any],
    escape_html: bool = False
) -> str:
    """
    Interpolate variables into a message string.

    Supports:
    - {{variable}} - Simple replacement
    - {{variable, type}} - Formatted replacement (number, currency, date)

    Args:
        message: Message string with placeholders
        variables: Dictionary of variable values
        escape_html: Whether to escape HTML in values

    Returns:
        Interpolated string

    Examples:
        interpolate("Hello, {{name}}!", {"name": "John"})
        # "Hello, John!"

        interpolate("Total: {{amount, currency}}", {"amount": 1000})
        # "Total: $1,000.00"
    """
    if not variables:
        return message

    pattern = re.compile(r'\{\{(\w+)(?:,\s*(\w+))?\}\}')

    def replace(match):
        var_name = match.group(1)
        format_type = match.group(2)

        if var_name not in variables:
            return match.group(0)

        value = variables[var_name]

        if format_type:
            value = format_value(value, format_type)
        else:
            value = str(value)

        if escape_html:
            value = html.escape(value)

        return value

    return pattern.sub(replace, message)


def format_value(value: Any, format_type: str) -> str:
    """
    Format a value based on type.

    Supported formats:
    - number: Format as number
    - currency: Format as currency
    - date: Format as date
    - time: Format as time
    - percent: Format as percentage
    """
    from app.i18n.core.context import get_locale
    locale = get_locale()

    if format_type == "number":
        return format_number(value, locale)

    elif format_type == "currency":
        return format_currency_inline(value, locale)

    elif format_type == "date":
        return format_date_inline(value, locale)

    elif format_type == "time":
        return format_time_inline(value, locale)

    elif format_type == "percent":
        return format_percent(value, locale)

    return str(value)


def format_number(value: Any, locale) -> str:
    """Format number according to locale."""
    try:
        num = float(value)
        decimal_sep = locale.number_format.decimal_separator
        thousands_sep = locale.number_format.thousands_separator

        if num == int(num):
            formatted = f"{int(num):,}".replace(",", thousands_sep)
        else:
            formatted = f"{num:,.2f}".replace(",", "TEMP").replace(".", decimal_sep).replace("TEMP", thousands_sep)

        return formatted
    except (ValueError, TypeError):
        return str(value)


def format_currency_inline(value: Any, locale) -> str:
    """Format currency according to locale."""
    try:
        num = float(value)
        symbol = locale.currency_symbol
        position = locale.currency_position

        formatted_num = format_number(num, locale)

        if position == "before":
            return f"{symbol}{formatted_num}"
        else:
            return f"{formatted_num} {symbol}"
    except (ValueError, TypeError):
        return str(value)


def format_date_inline(value: Any, locale) -> str:
    """Format date according to locale."""
    from datetime import datetime, date

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value

    if isinstance(value, (datetime, date)):
        fmt = locale.date_format
        fmt = fmt.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
        return value.strftime(fmt)

    return str(value)


def format_time_inline(value: Any, locale) -> str:
    """Format time according to locale."""
    from datetime import datetime, time

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value

    if isinstance(value, (datetime, time)):
        if locale.time_format == "12h":
            return value.strftime("%I:%M %p")
        else:
            return value.strftime("%H:%M")

    return str(value)


def format_percent(value: Any, locale) -> str:
    """Format percentage according to locale."""
    try:
        num = float(value)
        decimal_sep = locale.number_format.decimal_separator
        return f"{num:.1f}%".replace(".", decimal_sep)
    except (ValueError, TypeError):
        return str(value)
