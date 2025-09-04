"""Timezone utilities and datetime parsing for ocalcli."""

import os
from datetime import datetime, timezone
from typing import Optional, Union

import dateutil.parser
from dateutil import tz


def get_system_timezone() -> str:
    """Get the system's default timezone.
    
    Returns:
        Timezone string (e.g., 'Europe/Dublin')
    """
    # Try to get from environment first
    if tz_name := os.getenv("OCALCLI_TZ"):
        return tz_name
    
    # Get system timezone
    try:
        local_tz = tz.tzlocal()
        return str(local_tz)
    except Exception:
        # Fallback to UTC
        return "UTC"


def parse_datetime(
    dt_str: str, 
    timezone_name: Optional[str] = None
) -> datetime:
    """Parse a datetime string and make it timezone-aware.
    
    Args:
        dt_str: Datetime string to parse
        timezone_name: Timezone to apply if dt_str is naive
        
    Returns:
        Timezone-aware datetime
        
    Raises:
        ValueError: If datetime string is invalid
    """
    # Parse the datetime string
    try:
        dt = dateutil.parser.parse(dt_str)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid datetime string '{dt_str}': {e}")
    
    # If it's already timezone-aware, return as-is
    if dt.tzinfo is not None:
        return dt
    
    # Apply timezone if provided
    if timezone_name:
        tz_obj = tz.gettz(timezone_name)
        if tz_obj is None:
            raise ValueError(f"Unknown timezone: {timezone_name}")
        return dt.replace(tzinfo=tz_obj)
    
    # Use system timezone as fallback
    system_tz = get_system_timezone()
    tz_obj = tz.gettz(system_tz)
    if tz_obj is None:
        tz_obj = timezone.utc
    return dt.replace(tzinfo=tz_obj)


def format_for_graph(dt: datetime) -> tuple[str, str]:
    """Format datetime for Microsoft Graph API.
    
    Args:
        dt: Timezone-aware datetime
        
    Returns:
        Tuple of (iso_datetime, timezone_name)
    """
    if dt.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware")
    
    # Convert to ISO format
    iso_str = dt.isoformat()
    
    # Get timezone name
    if hasattr(dt.tzinfo, 'zone'):
        tz_name = dt.tzinfo.zone
    else:
        # Fallback to UTC offset
        offset = dt.tzinfo.utcoffset(dt)
        if offset:
            hours = offset.total_seconds() / 3600
            tz_name = f"UTC{hours:+d}"
        else:
            tz_name = "UTC"
    
    return iso_str, tz_name


def parse_date_range(
    start_str: Optional[str] = None,
    end_str: Optional[str] = None,
    timezone_name: Optional[str] = None
) -> tuple[datetime, datetime]:
    """Parse start and end date strings into timezone-aware datetimes.
    
    Args:
        start_str: Start date string (defaults to today)
        end_str: End date string (defaults to start + 7 days)
        timezone_name: Timezone to apply
        
    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    tz_name = timezone_name or get_system_timezone()
    
    if start_str:
        start_dt = parse_datetime(start_str, tz_name)
    else:
        # Default to today at midnight
        now = datetime.now(tz.gettz(tz_name))
        start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if end_str:
        end_dt = parse_datetime(end_str, tz_name)
    else:
        # Default to start + 7 days
        from datetime import timedelta
        end_dt = start_dt + timedelta(days=7)
    
    return start_dt, end_dt


def is_all_day_event(start: datetime, end: datetime) -> bool:
    """Check if an event should be treated as all-day.
    
    Args:
        start: Event start datetime
        end: Event end datetime
        
    Returns:
        True if event is all-day
    """
    # All-day if start is midnight and end is next midnight
    return (start.hour == 0 and start.minute == 0 and start.second == 0 and
            end.hour == 0 and end.minute == 0 and end.second == 0 and
            start.date() != end.date())


def normalize_all_day_event(start: datetime, end: datetime) -> tuple[datetime, datetime]:
    """Normalize all-day event times to midnight boundaries.
    
    Args:
        start: Event start datetime
        end: Event end datetime
        
    Returns:
        Tuple of normalized (start, end) datetimes
    """
    # Ensure start is at midnight
    start_normalized = start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Ensure end is at midnight of the next day
    end_normalized = end.replace(hour=0, minute=0, second=0, microsecond=0)
    
    return start_normalized, end_normalized
