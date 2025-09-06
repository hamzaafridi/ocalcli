"""Base calendar provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterable, Optional

from ..models import Event
from ..exceptions import EventNotFoundError, AuthenticationError, APIError


class CalendarProvider(ABC):
    """Abstract base class for calendar providers."""
    
    @abstractmethod
    def agenda(
        self, 
        start: datetime, 
        end: datetime, 
        query: Optional[str] = None
    ) -> Iterable[Event]:
        """Get events in the specified time range.
        
        Args:
            start: Start datetime (timezone-aware)
            end: End datetime (timezone-aware)
            query: Optional search query
            
        Returns:
            Iterable of Event objects
        """
        ...
    
    @abstractmethod
    def get(self, event_id: str) -> Event:
        """Get a specific event by ID.
        
        Args:
            event_id: Event identifier
            
        Returns:
            Event object
            
        Raises:
            EventNotFoundError: If event doesn't exist
        """
        ...
    
    @abstractmethod
    def add(self, event: Event) -> Event:
        """Create a new event.
        
        Args:
            event: Event to create (id will be ignored)
            
        Returns:
            Created event with assigned ID
        """
        ...
    
    @abstractmethod
    def edit(self, event_id: str, patch: dict) -> Event:
        """Update an existing event.
        
        Args:
            event_id: Event identifier
            patch: Dictionary of fields to update
            
        Returns:
            Updated event
            
        Raises:
            EventNotFoundError: If event doesn't exist
        """
        ...
    
    @abstractmethod
    def delete(self, event_id: str) -> None:
        """Delete an event.
        
        Args:
            event_id: Event identifier
            
        Raises:
            EventNotFoundError: If event doesn't exist
        """
        ...
    
    @abstractmethod
    def search(self, query: str, start: Optional[datetime] = None, end: Optional[datetime] = None) -> Iterable[Event]:
        """Search for events.
        
        Args:
            query: Search query
            start: Optional start datetime filter
            end: Optional end datetime filter
            
        Returns:
            Iterable of matching Event objects
        """
        ...
    
    @abstractmethod
    def import_ics(self, ics_content: str, calendar_id: Optional[str] = None) -> int:
        """Import events from ICS content.
        
        Args:
            ics_content: ICS file content
            calendar_id: Optional target calendar ID
            
        Returns:
            Number of events imported
        """
        ...


