"""Natural language event parsing for ocalcli quickadd."""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

from .models import Event
from .timeutils import parse_datetime, get_system_timezone


def parse_quickadd(text: str, timezone_name: Optional[str] = None) -> Event:
    """Parse natural language text into an Event.
    
    Args:
        text: Natural language text (e.g., "Tomorrow 4pm: Coffee with Ali @ Cafe Nero")
        timezone_name: Optional timezone to use
        
    Returns:
        Parsed Event object
        
    Raises:
        ValueError: If text cannot be parsed
    """
    tz_name = timezone_name or get_system_timezone()
    
    # Clean up the text
    text = text.strip()
    
    # Try to extract time and subject
    time_patterns = [
        # "Tomorrow 4pm: Subject"
        r"(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)\s*:\s*(.+)",
        # "4pm tomorrow: Subject"
        r"(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)\s+(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s*:\s*(.+)",
        # "Tomorrow: Subject" (no time, default to 9am)
        r"(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s*:\s*(.+)",
        # "4pm: Subject" (today)
        r"(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)\s*:\s*(.+)",
    ]
    
    parsed_event = None
    
    for pattern in time_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            
            if len(groups) == 3:
                # Pattern with time and day
                if groups[0].lower() in ["tomorrow", "today", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                    day_part = groups[0]
                    time_part = groups[1]
                    subject_part = groups[2]
                else:
                    time_part = groups[0]
                    day_part = groups[1]
                    subject_part = groups[2]
            elif len(groups) == 2:
                if groups[0].lower() in ["tomorrow", "today", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                    # Day only, no time
                    day_part = groups[0]
                    time_part = "9am"
                    subject_part = groups[1]
                else:
                    # Time only, assume today
                    time_part = groups[0]
                    day_part = "today"
                    subject_part = groups[1]
            else:
                continue
            
            # Parse the datetime
            start_dt = _parse_datetime_from_parts(day_part, time_part, tz_name)
            
            # Extract subject and location
            subject, location = _extract_subject_and_location(subject_part)
            
            # Default duration is 30 minutes
            end_dt = start_dt + timedelta(minutes=30)
            
            parsed_event = Event(
                subject=subject,
                location=location,
                start=start_dt,
                end=end_dt,
                all_day=False
            )
            break
    
    if not parsed_event:
        # Fallback: treat entire text as subject, default to today 9am
        now = datetime.now()
        start_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        end_dt = start_dt + timedelta(minutes=30)
        
        subject, location = _extract_subject_and_location(text)
        
        parsed_event = Event(
            subject=subject,
            location=location,
            start=start_dt,
            end=end_dt,
            all_day=False
        )
    
    return parsed_event


def _parse_datetime_from_parts(day_part: str, time_part: str, timezone_name: str) -> datetime:
    """Parse datetime from day and time parts."""
    now = datetime.now()
    
    # Parse day
    day_lower = day_part.lower()
    if day_lower == "today":
        target_date = now.date()
    elif day_lower == "tomorrow":
        target_date = now.date() + timedelta(days=1)
    elif day_lower in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        # Find next occurrence of this day
        days_ahead = _get_days_until_weekday(day_lower)
        target_date = now.date() + timedelta(days=days_ahead)
    else:
        target_date = now.date()
    
    # Parse time
    time_str = time_part.strip()
    
    # Handle AM/PM
    is_pm = False
    if "pm" in time_str.lower():
        is_pm = True
        time_str = time_str.replace("pm", "").replace("PM", "").strip()
    elif "am" in time_str.lower():
        time_str = time_str.replace("am", "").replace("AM", "").strip()
    
    # Parse hour and minute
    if ":" in time_str:
        hour_str, minute_str = time_str.split(":", 1)
        hour = int(hour_str)
        minute = int(minute_str)
    else:
        try:
            hour = int(time_str)
            minute = 0
        except ValueError:
            # Fallback to 9am if parsing fails
            hour = 9
            minute = 0
    
    # Convert to 24-hour format
    if is_pm and hour != 12:
        hour += 12
    elif not is_pm and hour == 12:
        hour = 0
    
    
    # Create datetime
    dt = datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute))
    
    # Apply timezone
    try:
        import pytz
        tz_obj = pytz.timezone(timezone_name)
        dt = tz_obj.localize(dt)
    except (ImportError, pytz.exceptions.UnknownTimeZoneError):
        # Fallback to dateutil
        from dateutil import tz
        tz_obj = tz.gettz(timezone_name)
        if tz_obj:
            dt = dt.replace(tzinfo=tz_obj)
    
    return dt


def _get_days_until_weekday(weekday: str) -> int:
    """Get days until next occurrence of weekday."""
    weekday_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }
    
    target_weekday = weekday_map[weekday.lower()]
    today_weekday = datetime.now().weekday()
    
    days_ahead = target_weekday - today_weekday
    if days_ahead <= 0:
        days_ahead += 7
    
    return days_ahead


def _extract_subject_and_location(text: str) -> Tuple[str, Optional[str]]:
    """Extract subject and location from text.
    
    Looks for patterns like "Subject @ Location" or "Subject at Location"
    """
    # Look for @ or "at" patterns
    at_patterns = [
        r"(.+?)\s+@\s+(.+)",
        r"(.+?)\s+at\s+(.+)",
    ]
    
    for pattern in at_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            subject = match.group(1).strip()
            location = match.group(2).strip()
            return subject, location
    
    # No location found
    return text.strip(), None
