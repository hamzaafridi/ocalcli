#!/usr/bin/env python3
"""Demo script for ocalcli functionality."""

import sys
from datetime import datetime, timezone

# Add current directory to path
sys.path.insert(0, '.')

from ocalcli.models import Event, Recurrence, Reminder, from_graph_event, to_graph_event
from ocalcli.quickadd import parse_quickadd
from ocalcli.timeutils import parse_datetime, format_for_graph


def demo_models():
    """Demonstrate the Event model functionality."""
    print("=== Event Model Demo ===")
    
    # Create a simple event
    event = Event(
        subject="Team Meeting",
        body="Weekly team sync",
        location="Conference Room A",
        start=datetime(2025, 1, 15, 14, 0, tzinfo=timezone.utc),
        end=datetime(2025, 1, 15, 15, 0, tzinfo=timezone.utc),
        attendees=["alice@company.com", "bob@company.com"],
        reminders=Reminder(minutes_before_start=15)
    )
    
    print(f"Created event: {event.subject}")
    print(f"Start: {event.start}")
    print(f"End: {event.end}")
    print(f"Location: {event.location}")
    print(f"Attendees: {event.attendees}")
    print(f"Reminder: {event.reminders.minutes_before_start} minutes before")
    
    # Convert to Graph format
    graph_event = to_graph_event(event)
    print(f"\nGraph format subject: {graph_event['subject']}")
    print(f"Graph format location: {graph_event['location']['displayName']}")
    
    # Convert back from Graph format
    restored_event = from_graph_event(graph_event)
    print(f"\nRestored event subject: {restored_event.subject}")
    print(f"Restored event location: {restored_event.location}")


def demo_quickadd():
    """Demonstrate the quickadd functionality."""
    print("\n=== Quickadd Demo ===")
    
    test_cases = [
        "Tomorrow 4pm: Coffee with Ali @ Cafe Nero",
        "Monday 9am: Standup meeting",
        "Today 2pm: Client call",
        "Next Friday: All day conference"
    ]
    
    for text in test_cases:
        print(f"\nInput: '{text}'")
        event = parse_quickadd(text)
        print(f"  Subject: {event.subject}")
        print(f"  Location: {event.location}")
        print(f"  Start: {event.start}")
        print(f"  End: {event.end}")


def demo_timeutils():
    """Demonstrate the timezone utilities."""
    print("\n=== Timezone Utils Demo ===")
    
    # Parse a datetime string
    dt = parse_datetime("2025-01-15T14:30:00", "Europe/Dublin")
    print(f"Parsed datetime: {dt}")
    
    # Format for Graph API
    iso_str, tz_name = format_for_graph(dt)
    print(f"Graph format: {iso_str} ({tz_name})")


def demo_recurrence():
    """Demonstrate recurrence functionality."""
    print("\n=== Recurrence Demo ===")
    
    # Create a recurring event
    recurrence = Recurrence(
        frequency="WEEKLY",
        interval=1,
        days_of_week=["monday", "wednesday", "friday"]
    )
    
    event = Event(
        subject="Daily Standup",
        start=datetime(2025, 1, 15, 9, 0, tzinfo=timezone.utc),
        end=datetime(2025, 1, 15, 9, 30, tzinfo=timezone.utc),
        recurrence=recurrence
    )
    
    print(f"Recurring event: {event.subject}")
    print(f"Frequency: {event.recurrence.frequency}")
    print(f"Days: {event.recurrence.days_of_week}")


if __name__ == "__main__":
    print("ocalcli - Outlook Calendar CLI Demo")
    print("=" * 40)
    
    try:
        demo_models()
        demo_quickadd()
        demo_timeutils()
        demo_recurrence()
        
        print("\n" + "=" * 40)
        print("Demo completed successfully!")
        print("\nTo use ocalcli with Microsoft Graph:")
        print("1. Run: ocalcli configure")
        print("2. Follow the authentication prompts")
        print("3. Use commands like: ocalcli agenda")
        
    except Exception as e:
        print(f"Demo failed: {e}")
        sys.exit(1)
