"""
Built-in functions for workflow expressions.
"""
from typing import Any, List, Optional
from datetime import datetime, timedelta
import re
import math


def fn_upper(text: Any) -> str:
    """Convert to uppercase."""
    return str(text).upper() if text else ''


def fn_lower(text: Any) -> str:
    """Convert to lowercase."""
    return str(text).lower() if text else ''


def fn_concat(*args) -> str:
    """Concatenate strings."""
    return ''.join(str(arg) for arg in args)


def fn_length(text: Any) -> int:
    """Get string length."""
    return len(str(text)) if text else 0


def fn_trim(text: Any) -> str:
    """Trim whitespace."""
    return str(text).strip() if text else ''


def fn_now() -> str:
    """Get current timestamp."""
    return datetime.utcnow().isoformat()


def fn_today() -> str:
    """Get current date."""
    return datetime.utcnow().strftime('%Y-%m-%d')


def fn_date_add(date_str: str, amount: int, unit: str = 'days') -> str:
    """Add time to a date."""
    try:
        if isinstance(date_str, datetime):
            date = date_str
        else:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

        units = {
            'seconds': timedelta(seconds=amount),
            'minutes': timedelta(minutes=amount),
            'hours': timedelta(hours=amount),
            'days': timedelta(days=amount),
            'weeks': timedelta(weeks=amount),
        }

        delta = units.get(unit, timedelta(days=amount))
        return (date + delta).isoformat()

    except Exception:
        return date_str


def fn_date_diff(date1: str, date2: str, unit: str = 'days') -> int:
    """Calculate difference between dates."""
    try:
        if isinstance(date1, datetime):
            d1 = date1
        else:
            d1 = datetime.fromisoformat(date1.replace('Z', '+00:00'))

        if isinstance(date2, datetime):
            d2 = date2
        else:
            d2 = datetime.fromisoformat(date2.replace('Z', '+00:00'))

        diff = d1 - d2

        units = {
            'seconds': diff.total_seconds(),
            'minutes': diff.total_seconds() / 60,
            'hours': diff.total_seconds() / 3600,
            'days': diff.days,
            'weeks': diff.days / 7,
        }

        return int(units.get(unit, diff.days))

    except Exception:
        return 0


def fn_format_date(date_str: str, fmt: str = '%Y-%m-%d') -> str:
    """Format a date."""
    try:
        if isinstance(date_str, datetime):
            date = date_str
        else:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

        fmt = fmt.replace('YYYY', '%Y')
        fmt = fmt.replace('MM', '%m')
        fmt = fmt.replace('DD', '%d')
        fmt = fmt.replace('HH', '%H')
        fmt = fmt.replace('mm', '%M')
        fmt = fmt.replace('ss', '%S')

        return date.strftime(fmt)

    except Exception:
        return date_str


def fn_format_currency(amount: Any, currency: str = 'USD') -> str:
    """Format a currency amount."""
    try:
        amount = float(amount)

        symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥',
        }

        symbol = symbols.get(currency, currency + ' ')

        if currency == 'JPY':
            return f"{symbol}{amount:,.0f}"

        return f"{symbol}{amount:,.2f}"

    except Exception:
        return str(amount)


def fn_round(number: Any, decimals: int = 0) -> float:
    """Round a number."""
    try:
        return round(float(number), decimals)
    except Exception:
        return 0


def fn_floor(number: Any) -> int:
    """Round down."""
    try:
        return math.floor(float(number))
    except Exception:
        return 0


def fn_ceil(number: Any) -> int:
    """Round up."""
    try:
        return math.ceil(float(number))
    except Exception:
        return 0


def fn_abs(number: Any) -> float:
    """Absolute value."""
    try:
        return abs(float(number))
    except Exception:
        return 0


def fn_min(*args) -> float:
    """Minimum value."""
    try:
        values = [float(arg) for arg in args if arg is not None]
        return min(values) if values else 0
    except Exception:
        return 0


def fn_max(*args) -> float:
    """Maximum value."""
    try:
        values = [float(arg) for arg in args if arg is not None]
        return max(values) if values else 0
    except Exception:
        return 0


def fn_sum(items: List) -> float:
    """Sum of items."""
    try:
        if not isinstance(items, list):
            items = [items]
        return sum(float(item) for item in items if item is not None)
    except Exception:
        return 0


def fn_avg(items: List) -> float:
    """Average of items."""
    try:
        if not isinstance(items, list):
            items = [items]
        values = [float(item) for item in items if item is not None]
        return sum(values) / len(values) if values else 0
    except Exception:
        return 0


def fn_count(items: List) -> int:
    """Count items."""
    try:
        if not isinstance(items, list):
            return 1 if items else 0
        return len(items)
    except Exception:
        return 0


def fn_if(condition: Any, true_value: Any, false_value: Any) -> Any:
    """Conditional value."""
    return true_value if condition else false_value


def fn_coalesce(*args) -> Any:
    """First non-null value."""
    for arg in args:
        if arg is not None:
            return arg
    return None


def fn_in(value: Any, items: List) -> bool:
    """Check if value is in list."""
    if not isinstance(items, list):
        items = [items]
    return value in items


BUILTIN_FUNCTIONS = {
    'UPPER': fn_upper,
    'LOWER': fn_lower,
    'CONCAT': fn_concat,
    'LENGTH': fn_length,
    'TRIM': fn_trim,
    'NOW': fn_now,
    'TODAY': fn_today,
    'DATE_ADD': fn_date_add,
    'DATE_DIFF': fn_date_diff,
    'FORMAT_DATE': fn_format_date,
    'FORMAT_CURRENCY': fn_format_currency,
    'ROUND': fn_round,
    'FLOOR': fn_floor,
    'CEIL': fn_ceil,
    'ABS': fn_abs,
    'MIN': fn_min,
    'MAX': fn_max,
    'SUM': fn_sum,
    'AVG': fn_avg,
    'COUNT': fn_count,
    'IF': fn_if,
    'COALESCE': fn_coalesce,
    'IN': fn_in,
}
