"""Event models and data structures for ocalcli."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Recurrence:
    """Recurrence pattern for events."""
    frequency: str  # DAILY, WEEKLY, MONTHLY, YEARLY
    interval: int = 1
    days_of_week: Optional[list[str]] = None  # monday, tuesday, etc.
    end_date: Optional[datetime] = None
    count: Optional[int] = None


@dataclass
class Reminder:
    """Reminder settings for events."""
    minutes_before_start: int = 15
    is_enabled: bool = True


@dataclass
class Event:
    """Normalized event model for ocalcli."""
    id: Optional[str] = None
    subject: str = ""
    body: Optional[str] = None
    location: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    all_day: bool = False
    attendees: list[str] = field(default_factory=list)
    recurrence: Optional[Recurrence] = None
    reminders: Optional[Reminder] = None
    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate event data after initialization."""
        if self.start and self.end and self.start >= self.end:
            raise ValueError("Event start time must be before end time")
        
        if self.all_day and self.start and self.end:
            # For all-day events, ensure they're on the same day
            if self.start.date() != self.end.date():
                raise ValueError("All-day events must start and end on the same day")


def from_graph_event(data: dict[str, Any]) -> Event:
    """Convert Microsoft Graph event to ocalcli Event model."""
    # Extract basic fields
    event_id = data.get("id")
    subject = data.get("subject", "")
    body_content = data.get("body", {}).get("content", "")
    location = data.get("location", {}).get("displayName")
    
    # Parse start/end times
    start_dt = None
    end_dt = None
    all_day = data.get("isAllDay", False)
    
    if start_data := data.get("start"):
        if all_day:
            # All-day events use date only
            start_dt = datetime.fromisoformat(start_data["dateTime"][:10])
        else:
            # Normalize microseconds to 6 decimal places for Python compatibility
            dt_str = start_data["dateTime"].replace("Z", "+00:00")
            if '.' in dt_str:
                # Find the decimal point and timezone separator
                dot_pos = dt_str.find('.')
                tz_pos = dt_str.find('+', dot_pos)
                if tz_pos == -1:
                    tz_pos = dt_str.find('-', dot_pos)
                if tz_pos == -1:
                    tz_pos = len(dt_str)
                
                # Extract microseconds part
                microsec_part = dt_str[dot_pos + 1:tz_pos]
                if len(microsec_part) > 6:
                    # Truncate to 6 decimal places
                    microsec_part = microsec_part[:6]
                elif len(microsec_part) < 6:
                    # Pad with zeros to 6 decimal places
                    microsec_part = microsec_part.ljust(6, '0')
                
                # Reconstruct the datetime string
                dt_str = dt_str[:dot_pos + 1] + microsec_part + dt_str[tz_pos:]
            
            start_dt = datetime.fromisoformat(dt_str)
    
    if end_data := data.get("end"):
        if all_day:
            end_dt = datetime.fromisoformat(end_data["dateTime"][:10])
        else:
            # Normalize microseconds to 6 decimal places for Python compatibility
            dt_str = end_data["dateTime"].replace("Z", "+00:00")
            if '.' in dt_str:
                # Find the decimal point and timezone separator
                dot_pos = dt_str.find('.')
                tz_pos = dt_str.find('+', dot_pos)
                if tz_pos == -1:
                    tz_pos = dt_str.find('-', dot_pos)
                if tz_pos == -1:
                    tz_pos = len(dt_str)
                
                # Extract microseconds part
                microsec_part = dt_str[dot_pos + 1:tz_pos]
                if len(microsec_part) > 6:
                    # Truncate to 6 decimal places
                    microsec_part = microsec_part[:6]
                elif len(microsec_part) < 6:
                    # Pad with zeros to 6 decimal places
                    microsec_part = microsec_part.ljust(6, '0')
                
                # Reconstruct the datetime string
                dt_str = dt_str[:dot_pos + 1] + microsec_part + dt_str[tz_pos:]
            
            end_dt = datetime.fromisoformat(dt_str)
    
    # Parse attendees
    attendees = []
    for attendee in data.get("attendees", []):
        if email := attendee.get("emailAddress", {}).get("address"):
            attendees.append(email)
    
    # Parse recurrence
    recurrence = None
    if rec_data := data.get("recurrence"):
        pattern = rec_data.get("pattern", {})
        freq = pattern.get("type", "").upper()
        if freq in ["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]:
            recurrence = Recurrence(
                frequency=freq,
                interval=pattern.get("interval", 1),
                days_of_week=pattern.get("daysOfWeek"),
                end_date=datetime.fromisoformat(rec_data["range"]["startDate"]) if rec_data.get("range", {}).get("startDate") else None
            )
    
    # Parse reminders
    reminders = None
    if data.get("isReminderOn"):
        minutes = data.get("reminderMinutesBeforeStart", 15)
        reminders = Reminder(minutes_before_start=minutes, is_enabled=True)
    
    return Event(
        id=event_id,
        subject=subject,
        body=body_content,
        location=location,
        start=start_dt,
        end=end_dt,
        all_day=all_day,
        attendees=attendees,
        recurrence=recurrence,
        reminders=reminders,
        raw=data
    )


def to_graph_event(event: Event) -> dict[str, Any]:
    """Convert ocalcli Event model to Microsoft Graph event format."""
    data: dict[str, Any] = {
        "subject": event.subject,
    }
    
    # Body content
    if event.body:
        data["body"] = {
            "contentType": "text",
            "content": event.body
        }
    
    # Location
    if event.location:
        data["location"] = {
            "displayName": event.location
        }
    
    # Start/end times
    if event.start and event.end:
        if event.all_day:
            # All-day events use date format
            data["start"] = {
                "dateTime": event.start.strftime("%Y-%m-%dT00:00:00"),
                "timeZone": "UTC"
            }
            data["end"] = {
                "dateTime": event.end.strftime("%Y-%m-%dT00:00:00"),
                "timeZone": "UTC"
            }
        else:
            # Regular events with timezone
            # Use the timezone from the configuration or default to UTC
            from .config import Config
            config = Config()
            timezone_name = config.timezone or "UTC"
            
            data["start"] = {
                "dateTime": event.start.isoformat(),
                "timeZone": timezone_name
            }
            data["end"] = {
                "dateTime": event.end.isoformat(),
                "timeZone": timezone_name
            }
    
    data["isAllDay"] = event.all_day
    
    # Attendees
    if event.attendees:
        data["attendees"] = [
            {
                "emailAddress": {"address": email},
                "type": "required"
            }
            for email in event.attendees
        ]
    
    # Recurrence
    if event.recurrence:
        rec_data = {
            "pattern": {
                "type": event.recurrence.frequency.lower(),
                "interval": event.recurrence.interval
            },
            "range": {
                "type": "noEnd"
            }
        }
        
        if event.recurrence.days_of_week:
            rec_data["pattern"]["daysOfWeek"] = event.recurrence.days_of_week
        
        if event.recurrence.end_date:
            rec_data["range"]["type"] = "endDate"
            rec_data["range"]["endDate"] = event.recurrence.end_date.strftime("%Y-%m-%d")
        elif event.recurrence.count:
            rec_data["range"]["type"] = "numbered"
            rec_data["range"]["numberOfOccurrences"] = event.recurrence.count
        
        data["recurrence"] = rec_data
    
    # Reminders
    if event.reminders and event.reminders.is_enabled:
        data["isReminderOn"] = True
        data["reminderMinutesBeforeStart"] = event.reminders.minutes_before_start
    else:
        data["isReminderOn"] = False
    
    return data
