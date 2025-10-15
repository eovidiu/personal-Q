"""
ABOUTME: Timezone-aware datetime utilities for Python 3.12+ compatibility.
ABOUTME: Replaces deprecated datetime.utcnow() with timezone-aware alternatives.
"""

from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.

    Replacement for deprecated datetime.utcnow().
    Compatible with Python 3.12+.

    Returns:
        Timezone-aware datetime in UTC

    Example:
        >>> now = utcnow()
        >>> now.tzinfo
        datetime.timezone.utc
    """
    return datetime.now(timezone.utc)


def utcnow_naive() -> datetime:
    """
    Get current UTC time as naive datetime.

    Use for database compatibility when timezone-aware datetimes
    cause issues (e.g., SQLite without timezone support).

    Returns:
        Naive datetime in UTC

    Note:
        Prefer utcnow() when possible. Only use this for backward
        compatibility with systems that don't support timezone-aware datetimes.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def make_aware(dt: datetime, tz: timezone = timezone.utc) -> datetime:
    """
    Make a naive datetime timezone-aware.

    Args:
        dt: Naive datetime
        tz: Timezone to apply (default: UTC)

    Returns:
        Timezone-aware datetime

    Example:
        >>> naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        >>> aware_dt = make_aware(naive_dt)
        >>> aware_dt.tzinfo
        datetime.timezone.utc
    """
    if dt.tzinfo is not None:
        # Already timezone-aware
        return dt
    return dt.replace(tzinfo=tz)


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is in UTC timezone.

    Converts timezone-aware datetimes to UTC.
    Treats naive datetimes as already being in UTC.

    Args:
        dt: Datetime (aware or naive)

    Returns:
        Timezone-aware datetime in UTC

    Example:
        >>> import datetime as dt_module
        >>> eastern = dt_module.timezone(dt_module.timedelta(hours=-5))
        >>> dt_eastern = datetime(2024, 1, 1, 12, 0, 0, tzinfo=eastern)
        >>> dt_utc = ensure_utc(dt_eastern)
        >>> dt_utc.hour
        17  # Converted to UTC
    """
    if dt.tzinfo is None:
        # Assume naive datetime is already UTC
        return dt.replace(tzinfo=timezone.utc)

    # Convert to UTC if in different timezone
    return dt.astimezone(timezone.utc)


def to_naive_utc(dt: datetime) -> datetime:
    """
    Convert any datetime to naive UTC.

    Useful for database storage when timezone-aware datetimes
    are not supported.

    Args:
        dt: Datetime (aware or naive)

    Returns:
        Naive datetime in UTC
    """
    if dt.tzinfo is None:
        # Already naive, assume UTC
        return dt

    # Convert to UTC first, then remove timezone
    return dt.astimezone(timezone.utc).replace(tzinfo=None)
