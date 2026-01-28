"""
Timezone management utilities.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime.

    Prefer this over ``datetime.utcnow()`` which returns a naive datetime
    and is deprecated since Python 3.12.
    """
    return datetime.now(timezone.utc)


TIMEZONE_OFFSETS: Dict[str, int] = {
    "UTC": 0,
    "GMT": 0,
    "EST": -5,
    "EDT": -4,
    "CST": -6,
    "CDT": -5,
    "MST": -7,
    "MDT": -6,
    "PST": -8,
    "PDT": -7,
    "AST": -4,
    "NST": -3.5,
    "CET": 1,
    "CEST": 2,
    "EET": 2,
    "EEST": 3,
    "WET": 0,
    "WEST": 1,
    "IST": 5.5,
    "PKT": 5,
    "BST": 6,
    "ICT": 7,
    "WIB": 7,
    "WITA": 8,
    "WIT": 9,
    "CST_CHINA": 8,
    "JST": 9,
    "KST": 9,
    "ACST": 9.5,
    "AEST": 10,
    "NZST": 12,
    "NZDT": 13,
}

TIMEZONE_NAMES: Dict[str, str] = {
    "America/New_York": "EST",
    "America/Chicago": "CST",
    "America/Denver": "MST",
    "America/Los_Angeles": "PST",
    "America/Anchorage": "AKST",
    "Pacific/Honolulu": "HST",
    "Europe/London": "GMT",
    "Europe/Paris": "CET",
    "Europe/Berlin": "CET",
    "Europe/Madrid": "CET",
    "Europe/Rome": "CET",
    "Europe/Amsterdam": "CET",
    "Europe/Brussels": "CET",
    "Europe/Warsaw": "CET",
    "Europe/Moscow": "MSK",
    "Asia/Tokyo": "JST",
    "Asia/Seoul": "KST",
    "Asia/Shanghai": "CST_CHINA",
    "Asia/Hong_Kong": "HKT",
    "Asia/Singapore": "SGT",
    "Asia/Kolkata": "IST",
    "Asia/Dubai": "GST",
    "Australia/Sydney": "AEST",
    "Australia/Melbourne": "AEST",
    "Australia/Perth": "AWST",
    "Pacific/Auckland": "NZST",
    "America/Sao_Paulo": "BRT",
    "America/Mexico_City": "CST",
    "America/Buenos_Aires": "ART",
}


class SimpleTimezone(timezone):
    """Simple timezone implementation with name."""

    def __init__(self, offset_hours: float, name: str = ""):
        offset = timedelta(hours=offset_hours)
        super().__init__(offset, name)
        self._name = name

    def tzname(self, dt):
        return self._name

    def __repr__(self):
        return f"SimpleTimezone({self._name})"


class TimezoneManager:
    """Timezone management utilities."""

    @classmethod
    def get_timezone(cls, tz_name: str) -> Optional[timezone]:
        """
        Get timezone object by name.

        Args:
            tz_name: Timezone name (e.g., 'EST', 'America/New_York', 'UTC+5')
        """
        if tz_name == "UTC" or tz_name == "GMT":
            return timezone.utc

        if tz_name.startswith("UTC"):
            offset_str = tz_name[3:]
            if offset_str:
                try:
                    if ":" in offset_str:
                        sign = 1 if offset_str[0] != "-" else -1
                        offset_str = offset_str.lstrip("+-")
                        hours, minutes = map(int, offset_str.split(":"))
                        offset_hours = sign * (hours + minutes / 60)
                    else:
                        offset_hours = float(offset_str)
                    return SimpleTimezone(offset_hours, tz_name)
                except ValueError:
                    pass

        if tz_name in TIMEZONE_OFFSETS:
            return SimpleTimezone(TIMEZONE_OFFSETS[tz_name], tz_name)

        if tz_name in TIMEZONE_NAMES:
            abbrev = TIMEZONE_NAMES[tz_name]
            if abbrev in TIMEZONE_OFFSETS:
                return SimpleTimezone(TIMEZONE_OFFSETS[abbrev], tz_name)

        return None

    @classmethod
    def convert(
        cls,
        dt: datetime,
        from_tz: str,
        to_tz: str
    ) -> Optional[datetime]:
        """
        Convert datetime between timezones.

        Args:
            dt: Datetime to convert
            from_tz: Source timezone
            to_tz: Target timezone
        """
        source_tz = cls.get_timezone(from_tz)
        target_tz = cls.get_timezone(to_tz)

        if not source_tz or not target_tz:
            return None

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=source_tz)
        else:
            dt = dt.astimezone(source_tz)

        return dt.astimezone(target_tz)

    @classmethod
    def to_utc(cls, dt: datetime, from_tz: str) -> Optional[datetime]:
        """Convert datetime to UTC."""
        return cls.convert(dt, from_tz, "UTC")

    @classmethod
    def from_utc(cls, dt: datetime, to_tz: str) -> Optional[datetime]:
        """Convert datetime from UTC."""
        return cls.convert(dt, "UTC", to_tz)

    @classmethod
    def now_in_timezone(cls, tz_name: str) -> Optional[datetime]:
        """Get current time in specified timezone."""
        tz = cls.get_timezone(tz_name)
        if tz:
            return datetime.now(tz)
        return None

    @classmethod
    def get_offset_string(cls, tz_name: str) -> str:
        """Get offset string (e.g., '+05:00')."""
        tz = cls.get_timezone(tz_name)
        if not tz:
            return ""

        offset = tz.utcoffset(None)
        if offset is None:
            return "+00:00"

        total_seconds = int(offset.total_seconds())
        sign = "+" if total_seconds >= 0 else "-"
        total_seconds = abs(total_seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        return f"{sign}{hours:02d}:{minutes:02d}"

    @classmethod
    def get_common_timezones(cls) -> List[Dict[str, str]]:
        """Get list of common timezones."""
        common = [
            ("UTC", "Coordinated Universal Time"),
            ("America/New_York", "Eastern Time (US)"),
            ("America/Chicago", "Central Time (US)"),
            ("America/Denver", "Mountain Time (US)"),
            ("America/Los_Angeles", "Pacific Time (US)"),
            ("Europe/London", "London"),
            ("Europe/Paris", "Paris / Central European"),
            ("Europe/Berlin", "Berlin"),
            ("Europe/Moscow", "Moscow"),
            ("Asia/Dubai", "Dubai"),
            ("Asia/Kolkata", "India"),
            ("Asia/Shanghai", "China"),
            ("Asia/Tokyo", "Tokyo"),
            ("Australia/Sydney", "Sydney"),
            ("Pacific/Auckland", "Auckland"),
        ]

        result = []
        for tz_id, name in common:
            offset = cls.get_offset_string(tz_id)
            result.append({
                "id": tz_id,
                "name": name,
                "offset": offset,
                "label": f"(UTC{offset}) {name}",
            })

        return result


def convert_timezone(
    dt: datetime,
    from_tz: str,
    to_tz: str
) -> Optional[datetime]:
    """Shorthand for timezone conversion."""
    return TimezoneManager.convert(dt, from_tz, to_tz)


def get_user_timezone() -> str:
    """Get current user's timezone from context."""
    from app.i18n.core.context import get_locale
    locale = get_locale()
    return locale.timezone
