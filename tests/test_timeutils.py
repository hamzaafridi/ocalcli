"""Tests for ocalcli timeutils."""

import pytest
from datetime import datetime, timezone
from ocalcli.timeutils import (
    parse_datetime, 
    format_for_graph, 
    parse_date_range,
    is_all_day_event,
    normalize_all_day_event
)


def test_parse_datetime():
    """Test datetime parsing."""
    # Test with timezone
    dt = parse_datetime("2025-01-15T10:00:00", "UTC")
    assert dt.year == 2025
    assert dt.hour == 10
    assert dt.tzinfo is not None
    
    # Test naive datetime with timezone
    dt = parse_datetime("2025-01-15T10:00:00", "Europe/Dublin")
    assert dt.tzinfo is not None


def test_format_for_graph():
    """Test Graph formatting."""
    dt = datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc)
    iso_str, tz_name = format_for_graph(dt)
    
    assert "2025-01-15T10:00:00" in iso_str
    assert tz_name == "UTC"


def test_parse_date_range():
    """Test date range parsing."""
    start, end = parse_date_range("2025-01-15", "2025-01-16", "UTC")
    
    assert start.year == 2025
    assert start.month == 1
    assert start.day == 15
    assert end.day == 16


def test_is_all_day_event():
    """Test all-day event detection."""
    start = datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(2025, 1, 16, 0, 0, 0, tzinfo=timezone.utc)
    
    assert is_all_day_event(start, end) is True
    
    start = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    end = datetime(2025, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
    
    assert is_all_day_event(start, end) is False


def test_normalize_all_day_event():
    """Test all-day event normalization."""
    start = datetime(2025, 1, 15, 9, 30, 0, tzinfo=timezone.utc)
    end = datetime(2025, 1, 15, 17, 30, 0, tzinfo=timezone.utc)
    
    norm_start, norm_end = normalize_all_day_event(start, end)
    
    assert norm_start.hour == 0
    assert norm_start.minute == 0
    assert norm_end.hour == 0
    assert norm_end.minute == 0
