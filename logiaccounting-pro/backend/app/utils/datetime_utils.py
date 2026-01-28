"""
DateTime Utilities
Centralized datetime handling with timezone-aware UTC timestamps
"""
from datetime import datetime, timezone, timedelta
from typing import Optional


def utc_now() -> datetime:
    """
    Returns current UTC time as timezone-aware datetime.
    Use this instead of datetime.utcnow() which returns naive datetime.
    """
    return datetime.now(timezone.utc)


def utc_timestamp() -> float:
    """Returns current UTC time as Unix timestamp."""
    return utc_now().timestamp()


def utc_from_timestamp(ts: float) -> datetime:
    """Convert Unix timestamp to timezone-aware UTC datetime."""
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """
    Convert datetime to UTC.
    If naive, assumes UTC. If aware, converts to UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_expired(dt: datetime, max_age_seconds: int) -> bool:
    """Check if datetime is older than max_age_seconds from now."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return utc_now() - dt > timedelta(seconds=max_age_seconds)


def format_iso(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime as ISO 8601 string with timezone."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def parse_iso(iso_string: str) -> datetime:
    """Parse ISO 8601 string to timezone-aware datetime."""
    dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def start_of_day(dt: Optional[datetime] = None) -> datetime:
    """Get start of day (00:00:00) for given datetime or today."""
    if dt is None:
        dt = utc_now()
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: Optional[datetime] = None) -> datetime:
    """Get end of day (23:59:59.999999) for given datetime or today."""
    if dt is None:
        dt = utc_now()
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def days_ago(days: int) -> datetime:
    """Get datetime N days ago from now."""
    return utc_now() - timedelta(days=days)


def days_from_now(days: int) -> datetime:
    """Get datetime N days from now."""
    return utc_now() + timedelta(days=days)
