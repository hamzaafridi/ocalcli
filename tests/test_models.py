"""Tests for ocalcli models."""

import pytest
from datetime import datetime, timezone
from ocalcli.models import Event, Recurrence, Reminder, from_graph_event, to_graph_event


def test_event_creation():
    """Test basic event creation."""
    event = Event(
        subject="Test Event",
        start=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
        end=datetime(2025, 1, 15, 11, 0, tzinfo=timezone.utc)
    )
    
    assert event.subject == "Test Event"
    assert event.start.hour == 10
    assert event.end.hour == 11


def test_event_validation():
    """Test event validation."""
    # Valid event
    event = Event(
        subject="Test",
        start=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
        end=datetime(2025, 1, 15, 11, 0, tzinfo=timezone.utc)
    )
    assert event.subject == "Test"
    
    # Invalid: start >= end
    with pytest.raises(ValueError):
        Event(
            subject="Test",
            start=datetime(2025, 1, 15, 11, 0, tzinfo=timezone.utc),
            end=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc)
        )


def test_recurrence():
    """Test recurrence model."""
    recurrence = Recurrence(
        frequency="WEEKLY",
        interval=2,
        days_of_week=["monday", "wednesday"]
    )
    
    assert recurrence.frequency == "WEEKLY"
    assert recurrence.interval == 2
    assert recurrence.days_of_week == ["monday", "wednesday"]


def test_reminder():
    """Test reminder model."""
    reminder = Reminder(minutes_before_start=30, is_enabled=True)
    
    assert reminder.minutes_before_start == 30
    assert reminder.is_enabled is True


def test_from_graph_event():
    """Test conversion from Graph event."""
    graph_event = {
        "id": "test-id",
        "subject": "Test Event",
        "body": {"contentType": "text", "content": "Test description"},
        "location": {"displayName": "Test Location"},
        "start": {"dateTime": "2025-01-15T10:00:00Z", "timeZone": "UTC"},
        "end": {"dateTime": "2025-01-15T11:00:00Z", "timeZone": "UTC"},
        "isAllDay": False,
        "attendees": [
            {"emailAddress": {"address": "test@example.com"}, "type": "required"}
        ],
        "isReminderOn": True,
        "reminderMinutesBeforeStart": 15
    }
    
    event = from_graph_event(graph_event)
    
    assert event.id == "test-id"
    assert event.subject == "Test Event"
    assert event.body == "Test description"
    assert event.location == "Test Location"
    assert event.start.year == 2025
    assert event.end.hour == 11
    assert event.all_day is False
    assert event.attendees == ["test@example.com"]
    assert event.reminders.minutes_before_start == 15


def test_to_graph_event():
    """Test conversion to Graph event."""
    event = Event(
        id="test-id",
        subject="Test Event",
        body="Test description",
        location="Test Location",
        start=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
        end=datetime(2025, 1, 15, 11, 0, tzinfo=timezone.utc),
        all_day=False,
        attendees=["test@example.com"],
        reminders=Reminder(minutes_before_start=15)
    )
    
    graph_event = to_graph_event(event)
    
    assert graph_event["subject"] == "Test Event"
    assert graph_event["body"]["content"] == "Test description"
    assert graph_event["location"]["displayName"] == "Test Location"
    assert "2025-01-15T10:00:00" in graph_event["start"]["dateTime"]
    assert "2025-01-15T11:00:00" in graph_event["end"]["dateTime"]
    assert graph_event["isAllDay"] is False
    assert len(graph_event["attendees"]) == 1
    assert graph_event["attendees"][0]["emailAddress"]["address"] == "test@example.com"
    assert graph_event["isReminderOn"] is True
    assert graph_event["reminderMinutesBeforeStart"] == 15
