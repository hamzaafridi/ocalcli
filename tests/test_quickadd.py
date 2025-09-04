"""Tests for ocalcli quickadd."""

import pytest
from datetime import datetime
from ocalcli.quickadd import parse_quickadd


def test_parse_quickadd_tomorrow():
    """Test parsing tomorrow events."""
    event = parse_quickadd("Tomorrow 4pm: Coffee with Ali @ Cafe Nero")
    
    assert event.subject == "Coffee with Ali"
    assert event.location == "Cafe Nero"
    assert event.start.hour == 16  # 4pm


def test_parse_quickadd_today():
    """Test parsing today events."""
    event = parse_quickadd("Today 2pm: Meeting")
    
    assert event.subject == "Meeting"
    assert event.start.hour == 14  # 2pm


def test_parse_quickadd_weekday():
    """Test parsing weekday events."""
    event = parse_quickadd("Monday 9am: Standup")
    
    assert event.subject == "Standup"
    assert event.start.hour == 9


def test_parse_quickadd_no_time():
    """Test parsing events without time."""
    event = parse_quickadd("Tomorrow: All day event")
    
    assert event.subject == "All day event"
    assert event.start.hour == 9  # Default time


def test_parse_quickadd_no_location():
    """Test parsing events without location."""
    event = parse_quickadd("Tomorrow 3pm: Call with client")
    
    assert event.subject == "Call with client"
    assert event.location is None


def test_parse_quickadd_fallback():
    """Test fallback parsing."""
    event = parse_quickadd("Some random text")
    
    assert event.subject == "Some random text"
    assert event.start.hour == 9  # Default time
