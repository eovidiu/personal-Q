"""
ABOUTME: Tests for timezone-aware datetime utilities.
ABOUTME: Verifies Python 3.12+ compatibility and correct timezone handling.
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.utils.datetime_utils import (
    utcnow,
    utcnow_naive,
    make_aware,
    ensure_utc,
    to_naive_utc
)


class TestDatetimeUtils:
    """Test datetime utility functions."""

    def test_utcnow_is_aware(self):
        """Test that utcnow() returns timezone-aware datetime."""
        now = utcnow()
        assert now.tzinfo is not None
        assert now.tzinfo == timezone.utc

    def test_utcnow_is_recent(self):
        """Test that utcnow() returns recent time."""
        now = utcnow()
        # Should be within 1 second of actual time
        python_now = datetime.now(timezone.utc)
        diff = abs((now - python_now).total_seconds())
        assert diff < 1

    def test_utcnow_naive_is_naive(self):
        """Test that utcnow_naive() returns naive datetime."""
        now = utcnow_naive()
        assert now.tzinfo is None

    def test_utcnow_naive_is_utc(self):
        """Test that utcnow_naive() returns UTC time."""
        aware = utcnow()
        naive = utcnow_naive()
        # Convert naive to aware for comparison
        naive_aware = naive.replace(tzinfo=timezone.utc)
        diff = abs((aware - naive_aware).total_seconds())
        assert diff < 1

    def test_make_aware_from_naive(self):
        """Test making naive datetime timezone-aware."""
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        aware_dt = make_aware(naive_dt)
        
        assert aware_dt.tzinfo is not None
        assert aware_dt.tzinfo == timezone.utc
        assert aware_dt.year == 2024
        assert aware_dt.month == 1
        assert aware_dt.day == 1
        assert aware_dt.hour == 12

    def test_make_aware_already_aware(self):
        """Test that make_aware preserves already-aware datetime."""
        aware_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = make_aware(aware_dt)
        
        assert result.tzinfo == timezone.utc
        assert result == aware_dt

    def test_ensure_utc_from_naive(self):
        """Test ensuring naive datetime is in UTC."""
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        utc_dt = ensure_utc(naive_dt)
        
        assert utc_dt.tzinfo == timezone.utc
        assert utc_dt.hour == 12  # Assumed to be UTC

    def test_ensure_utc_from_different_timezone(self):
        """Test converting datetime from different timezone to UTC."""
        # Create datetime in EST (UTC-5)
        eastern = timezone(timedelta(hours=-5))
        dt_eastern = datetime(2024, 1, 1, 12, 0, 0, tzinfo=eastern)
        
        utc_dt = ensure_utc(dt_eastern)
        
        assert utc_dt.tzinfo == timezone.utc
        assert utc_dt.hour == 17  # 12 EST = 17 UTC

    def test_ensure_utc_already_utc(self):
        """Test that ensure_utc preserves UTC datetime."""
        utc_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = ensure_utc(utc_dt)
        
        assert result.tzinfo == timezone.utc
        assert result == utc_dt

    def test_to_naive_utc_from_aware(self):
        """Test converting aware datetime to naive UTC."""
        aware_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        naive_dt = to_naive_utc(aware_dt)
        
        assert naive_dt.tzinfo is None
        assert naive_dt.year == 2024
        assert naive_dt.hour == 12

    def test_to_naive_utc_from_different_timezone(self):
        """Test converting non-UTC aware datetime to naive UTC."""
        # Create datetime in EST (UTC-5)
        eastern = timezone(timedelta(hours=-5))
        dt_eastern = datetime(2024, 1, 1, 12, 0, 0, tzinfo=eastern)
        
        naive_utc = to_naive_utc(dt_eastern)
        
        assert naive_utc.tzinfo is None
        assert naive_utc.hour == 17  # 12 EST = 17 UTC

    def test_to_naive_utc_from_naive(self):
        """Test that to_naive_utc preserves naive datetime."""
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        result = to_naive_utc(naive_dt)
        
        assert result.tzinfo is None
        assert result == naive_dt

    def test_isoformat_includes_timezone(self):
        """Test that isoformat() includes timezone info."""
        now = utcnow()
        iso_str = now.isoformat()
        
        # Should include timezone offset
        assert '+00:00' in iso_str or 'Z' in iso_str

    def test_no_deprecation_warning(self):
        """Test that using utcnow() doesn't produce deprecation warnings."""
        # This test just ensures our utility works without warnings
        import warnings
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _ = utcnow()
            
            # Should not have any deprecation warnings
            deprecation_warnings = [
                warning for warning in w
                if issubclass(warning.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) == 0


class TestPython312Compatibility:
    """Test Python 3.12+ compatibility."""

    def test_uses_timezone_aware_objects(self):
        """Test that we use timezone-aware objects as recommended."""
        now = utcnow()
        
        # Must be timezone-aware
        assert now.tzinfo is not None
        
        # Must be UTC
        assert now.tzinfo == timezone.utc

    def test_replacement_for_datetime_utcnow(self):
        """Test that utcnow() is a proper replacement for datetime.utcnow()."""
        # Our utcnow()
        our_now = utcnow()

        # Python's deprecated utcnow() (for comparison)
        # Note: In Python 3.12+, utcnow() is deprecated but the warning may be
        # filtered by pytest configuration, so we don't check for it here
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            deprecated_now = datetime.utcnow()

        # Should be close in time (within 1 second)
        our_naive = our_now.replace(tzinfo=None)
        diff = abs((our_naive - deprecated_now).total_seconds())
        assert diff < 1

        # But ours should be timezone-aware
        assert our_now.tzinfo is not None
        assert deprecated_now.tzinfo is None

