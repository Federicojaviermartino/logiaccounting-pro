"""
Date and time formatting utilities.
"""
from datetime import datetime, date, time, timedelta
from typing import Optional, Union
from enum import Enum

from app.i18n.core.context import get_locale
from app.utils.datetime_utils import utc_now
from app.i18n.core.locale import LocaleContext


class DateFormat(str, Enum):
    """Predefined date formats."""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"
    FULL = "full"
    ISO = "iso"


class TimeFormat(str, Enum):
    """Predefined time formats."""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"
    ISO = "iso"


DATE_FORMATS = {
    "en": {
        DateFormat.SHORT: "%m/%d/%y",
        DateFormat.MEDIUM: "%b %d, %Y",
        DateFormat.LONG: "%B %d, %Y",
        DateFormat.FULL: "%A, %B %d, %Y",
        DateFormat.ISO: "%Y-%m-%d",
    },
    "es": {
        DateFormat.SHORT: "%d/%m/%y",
        DateFormat.MEDIUM: "%d %b %Y",
        DateFormat.LONG: "%d de %B de %Y",
        DateFormat.FULL: "%A, %d de %B de %Y",
        DateFormat.ISO: "%Y-%m-%d",
    },
    "de": {
        DateFormat.SHORT: "%d.%m.%y",
        DateFormat.MEDIUM: "%d. %b %Y",
        DateFormat.LONG: "%d. %B %Y",
        DateFormat.FULL: "%A, %d. %B %Y",
        DateFormat.ISO: "%Y-%m-%d",
    },
    "fr": {
        DateFormat.SHORT: "%d/%m/%y",
        DateFormat.MEDIUM: "%d %b %Y",
        DateFormat.LONG: "%d %B %Y",
        DateFormat.FULL: "%A %d %B %Y",
        DateFormat.ISO: "%Y-%m-%d",
    },
    "it": {
        DateFormat.SHORT: "%d/%m/%y",
        DateFormat.MEDIUM: "%d %b %Y",
        DateFormat.LONG: "%d %B %Y",
        DateFormat.FULL: "%A %d %B %Y",
        DateFormat.ISO: "%Y-%m-%d",
    },
    "ja": {
        DateFormat.SHORT: "%y/%m/%d",
        DateFormat.MEDIUM: "%Y年%m月%d日",
        DateFormat.LONG: "%Y年%m月%d日",
        DateFormat.FULL: "%Y年%m月%d日 %A",
        DateFormat.ISO: "%Y-%m-%d",
    },
    "ar": {
        DateFormat.SHORT: "%d/%m/%y",
        DateFormat.MEDIUM: "%d %b %Y",
        DateFormat.LONG: "%d %B %Y",
        DateFormat.FULL: "%A، %d %B %Y",
        DateFormat.ISO: "%Y-%m-%d",
    },
}

RELATIVE_UNITS = {
    "en": {
        "now": "just now",
        "seconds": "{n} seconds ago",
        "minute": "1 minute ago",
        "minutes": "{n} minutes ago",
        "hour": "1 hour ago",
        "hours": "{n} hours ago",
        "day": "yesterday",
        "days": "{n} days ago",
        "week": "1 week ago",
        "weeks": "{n} weeks ago",
        "month": "1 month ago",
        "months": "{n} months ago",
        "year": "1 year ago",
        "years": "{n} years ago",
        "future_seconds": "in {n} seconds",
        "future_minute": "in 1 minute",
        "future_minutes": "in {n} minutes",
        "future_hour": "in 1 hour",
        "future_hours": "in {n} hours",
        "future_day": "tomorrow",
        "future_days": "in {n} days",
    },
    "es": {
        "now": "ahora mismo",
        "seconds": "hace {n} segundos",
        "minute": "hace 1 minuto",
        "minutes": "hace {n} minutos",
        "hour": "hace 1 hora",
        "hours": "hace {n} horas",
        "day": "ayer",
        "days": "hace {n} días",
        "week": "hace 1 semana",
        "weeks": "hace {n} semanas",
        "month": "hace 1 mes",
        "months": "hace {n} meses",
        "year": "hace 1 año",
        "years": "hace {n} años",
        "future_seconds": "en {n} segundos",
        "future_minute": "en 1 minuto",
        "future_minutes": "en {n} minutos",
        "future_hour": "en 1 hora",
        "future_hours": "en {n} horas",
        "future_day": "mañana",
        "future_days": "en {n} días",
    },
    "de": {
        "now": "gerade eben",
        "seconds": "vor {n} Sekunden",
        "minute": "vor 1 Minute",
        "minutes": "vor {n} Minuten",
        "hour": "vor 1 Stunde",
        "hours": "vor {n} Stunden",
        "day": "gestern",
        "days": "vor {n} Tagen",
        "week": "vor 1 Woche",
        "weeks": "vor {n} Wochen",
        "month": "vor 1 Monat",
        "months": "vor {n} Monaten",
        "year": "vor 1 Jahr",
        "years": "vor {n} Jahren",
        "future_seconds": "in {n} Sekunden",
        "future_minute": "in 1 Minute",
        "future_minutes": "in {n} Minuten",
        "future_hour": "in 1 Stunde",
        "future_hours": "in {n} Stunden",
        "future_day": "morgen",
        "future_days": "in {n} Tagen",
    },
    "fr": {
        "now": "à l'instant",
        "seconds": "il y a {n} secondes",
        "minute": "il y a 1 minute",
        "minutes": "il y a {n} minutes",
        "hour": "il y a 1 heure",
        "hours": "il y a {n} heures",
        "day": "hier",
        "days": "il y a {n} jours",
        "week": "il y a 1 semaine",
        "weeks": "il y a {n} semaines",
        "month": "il y a 1 mois",
        "months": "il y a {n} mois",
        "year": "il y a 1 an",
        "years": "il y a {n} ans",
        "future_seconds": "dans {n} secondes",
        "future_minute": "dans 1 minute",
        "future_minutes": "dans {n} minutes",
        "future_hour": "dans 1 heure",
        "future_hours": "dans {n} heures",
        "future_day": "demain",
        "future_days": "dans {n} jours",
    },
}


class DateTimeFormatter:
    """Date and time formatting utilities."""

    @classmethod
    def format_date(
        cls,
        value: Union[datetime, date, str],
        format_type: DateFormat = DateFormat.MEDIUM,
        locale: Optional[LocaleContext] = None,
        custom_format: Optional[str] = None
    ) -> str:
        """
        Format date according to locale.

        Args:
            value: Date to format
            format_type: Predefined format type
            locale: Locale context (uses current if not provided)
            custom_format: Custom strftime format
        """
        if not locale:
            locale = get_locale()

        dt = cls._parse_datetime(value)
        if not dt:
            return str(value)

        if custom_format:
            return dt.strftime(custom_format)

        lang = locale.language.split("-")[0]
        formats = DATE_FORMATS.get(lang, DATE_FORMATS["en"])
        fmt = formats.get(format_type, formats[DateFormat.MEDIUM])

        return dt.strftime(fmt)

    @classmethod
    def format_time(
        cls,
        value: Union[datetime, time, str],
        locale: Optional[LocaleContext] = None,
        show_seconds: bool = False
    ) -> str:
        """
        Format time according to locale.

        Args:
            value: Time to format
            locale: Locale context
            show_seconds: Whether to show seconds
        """
        if not locale:
            locale = get_locale()

        dt = cls._parse_datetime(value)
        if not dt:
            return str(value)

        if locale.time_format == "12h":
            if show_seconds:
                return dt.strftime("%I:%M:%S %p")
            return dt.strftime("%I:%M %p")
        else:
            if show_seconds:
                return dt.strftime("%H:%M:%S")
            return dt.strftime("%H:%M")

    @classmethod
    def format_datetime(
        cls,
        value: Union[datetime, str],
        date_format: DateFormat = DateFormat.MEDIUM,
        locale: Optional[LocaleContext] = None,
        show_seconds: bool = False
    ) -> str:
        """
        Format datetime according to locale.

        Args:
            value: Datetime to format
            date_format: Date format type
            locale: Locale context
            show_seconds: Whether to show seconds in time
        """
        if not locale:
            locale = get_locale()

        dt = cls._parse_datetime(value)
        if not dt:
            return str(value)

        date_str = cls.format_date(dt, date_format, locale)
        time_str = cls.format_time(dt, locale, show_seconds)

        return f"{date_str} {time_str}"

    @classmethod
    def format_relative(
        cls,
        value: Union[datetime, str],
        locale: Optional[LocaleContext] = None,
        reference: Optional[datetime] = None
    ) -> str:
        """
        Format datetime as relative time (e.g., "2 hours ago").

        Args:
            value: Datetime to format
            locale: Locale context
            reference: Reference datetime (defaults to now)
        """
        if not locale:
            locale = get_locale()

        dt = cls._parse_datetime(value)
        if not dt:
            return str(value)

        ref = reference or utc_now()
        if dt.tzinfo:
            ref = ref.replace(tzinfo=dt.tzinfo)

        diff = ref - dt
        is_future = diff.total_seconds() < 0

        if is_future:
            diff = -diff

        lang = locale.language.split("-")[0]
        units = RELATIVE_UNITS.get(lang, RELATIVE_UNITS["en"])

        seconds = int(diff.total_seconds())
        minutes = seconds // 60
        hours = minutes // 60
        days = diff.days
        weeks = days // 7
        months = days // 30
        years = days // 365

        prefix = "future_" if is_future else ""

        if seconds < 30:
            return units["now"]
        elif seconds < 60:
            key = f"{prefix}seconds" if is_future else "seconds"
            return units.get(key, units["seconds"]).format(n=seconds)
        elif minutes == 1:
            key = f"{prefix}minute" if is_future else "minute"
            return units.get(key, units["minute"])
        elif minutes < 60:
            key = f"{prefix}minutes" if is_future else "minutes"
            return units.get(key, units["minutes"]).format(n=minutes)
        elif hours == 1:
            key = f"{prefix}hour" if is_future else "hour"
            return units.get(key, units["hour"])
        elif hours < 24:
            key = f"{prefix}hours" if is_future else "hours"
            return units.get(key, units["hours"]).format(n=hours)
        elif days == 1:
            key = f"{prefix}day" if is_future else "day"
            return units.get(key, units["day"])
        elif days < 7:
            key = f"{prefix}days" if is_future else "days"
            return units.get(key, units["days"]).format(n=days)
        elif weeks == 1:
            return units["week"]
        elif weeks < 4:
            return units["weeks"].format(n=weeks)
        elif months == 1:
            return units["month"]
        elif months < 12:
            return units["months"].format(n=months)
        elif years == 1:
            return units["year"]
        else:
            return units["years"].format(n=years)

    @classmethod
    def _parse_datetime(
        cls,
        value: Union[datetime, date, time, str]
    ) -> Optional[datetime]:
        """Parse value to datetime."""
        if isinstance(value, datetime):
            return value
        elif isinstance(value, date):
            return datetime.combine(value, time.min)
        elif isinstance(value, time):
            return datetime.combine(date.today(), value)
        elif isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
        return None


def format_date(
    value: Union[datetime, date, str],
    format_type: DateFormat = DateFormat.MEDIUM
) -> str:
    """Shorthand for date formatting."""
    return DateTimeFormatter.format_date(value, format_type)


def format_time(
    value: Union[datetime, time, str],
    show_seconds: bool = False
) -> str:
    """Shorthand for time formatting."""
    return DateTimeFormatter.format_time(value, show_seconds=show_seconds)


def format_datetime(
    value: Union[datetime, str],
    date_format: DateFormat = DateFormat.MEDIUM
) -> str:
    """Shorthand for datetime formatting."""
    return DateTimeFormatter.format_datetime(value, date_format)


def format_relative(value: Union[datetime, str]) -> str:
    """Shorthand for relative time formatting."""
    return DateTimeFormatter.format_relative(value)
