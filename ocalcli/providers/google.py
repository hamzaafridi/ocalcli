"""Google Calendar provider stub for ocalcli."""

from typing import Any, Dict, Iterable, Optional
from datetime import datetime

from .base import CalendarProvider


class GoogleProvider(CalendarProvider):
    """Google Calendar provider (stub implementation)."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the provider."""
        raise NotImplementedError("Google Calendar provider not yet implemented")
    
    def agenda(
        self, 
        start: datetime, 
        end: datetime, 
        query: Optional[str] = None
    ) -> Iterable[Any]:
        """Get events in the specified time range."""
        raise NotImplementedError("Google Calendar provider not yet implemented")
    
    def get(self, event_id: str) -> Any:
        """Get a specific event by ID."""
        raise NotImplementedError("Google Calendar provider not yet implemented")
    
    def add(self, event: Any) -> Any:
        """Create a new event."""
        raise NotImplementedError("Google Calendar provider not yet implemented")
    
    def edit(self, event_id: str, patch: Dict) -> Any:
        """Update an existing event."""
        raise NotImplementedError("Google Calendar provider not yet implemented")
    
    def delete(self, event_id: str) -> None:
        """Delete an event."""
        raise NotImplementedError("Google Calendar provider not yet implemented")
    
    def search(
        self, 
        query: str, 
        start: Optional[datetime] = None, 
        end: Optional[datetime] = None
    ) -> Iterable[Any]:
        """Search for events."""
        raise NotImplementedError("Google Calendar provider not yet implemented")
    
    def import_ics(self, ics_content: str, calendar_id: Optional[str] = None) -> int:
        """Import events from ICS content."""
        raise NotImplementedError("Google Calendar provider not yet implemented")
