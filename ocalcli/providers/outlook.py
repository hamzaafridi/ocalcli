"""Microsoft Graph provider for ocalcli."""

import json
from datetime import datetime
from typing import Any, Dict, Iterable, Optional

import httpx
from icalendar import Calendar as ICalendar

from ..auth.outlook_auth import OutlookAuth
from ..models import Event, from_graph_event, to_graph_event
from .base import CalendarProvider
from ..exceptions import APIError, AuthenticationError, EventNotFoundError


class OutlookProvider(CalendarProvider):
    """Microsoft Graph calendar provider."""
    
    BASE_URL = "https://graph.microsoft.com/v1.0"
    
    def __init__(self, auth: OutlookAuth, calendar_id: Optional[str] = None):
        """Initialize the provider.
        
        Args:
            auth: OutlookAuth instance
            calendar_id: Optional calendar ID (defaults to primary calendar)
        """
        self.auth = auth
        self.calendar_id = calendar_id or "primary"
        self._client: Optional[httpx.Client] = None
    
    def _get_client(self) -> httpx.Client:
        """Get authenticated HTTP client."""
        if self._client is None:
            token = self.auth.get_access_token()
            self._client = httpx.Client(
                base_url=self.BASE_URL,
                timeout=15.0,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
        return self._client
    
    def _make_request(
        self, 
        method: str, 
        url: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Make authenticated request to Microsoft Graph."""
        client = self._get_client()
        
        try:
            response = client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Authentication failed. Please run 'ocalcli configure' to re-authenticate.")
            elif e.response.status_code == 404:
                raise EventNotFoundError("Event not found")
            else:
                error_detail = "Unknown error"
                try:
                    error_data = e.response.json()
                    error_detail = error_data.get("error", {}).get("message", error_detail)
                except json.JSONDecodeError:
                    pass
                raise APIError(f"API request failed: {e.response.status_code} - {error_detail}")
        except httpx.RequestError as e:
            raise APIError(f"Network error: {e}")
    
    def agenda(
        self, 
        start: datetime, 
        end: datetime, 
        query: Optional[str] = None
    ) -> Iterable[Event]:
        """Get events in the specified time range."""
        # Format datetimes for Graph API
        start_iso = start.isoformat()
        end_iso = end.isoformat()
        
        # Build URL
        if self.calendar_id == "primary":
            url = "/me/calendar/calendarView"
        else:
            url = f"/me/calendars/{self.calendar_id}/calendarView"
        params = {
            "startDateTime": start_iso,
            "endDateTime": end_iso,
            "$orderby": "start/dateTime"
        }
        
        if query:
            params["$search"] = f'"{query}"'
            # Add header for search
            headers = {"ConsistencyLevel": "eventual"}
        else:
            headers = {}
        
        response = self._make_request("GET", url, params=params, headers=headers)
        
        for event_data in response.get("value", []):
            yield from_graph_event(event_data)
    
    def get(self, event_id: str) -> Event:
        """Get a specific event by ID."""
        if self.calendar_id == "primary":
            url = f"/me/calendar/events/{event_id}"
        else:
            url = f"/me/calendars/{self.calendar_id}/events/{event_id}"
        event_data = self._make_request("GET", url)
        return from_graph_event(event_data)
    
    def add(self, event: Event) -> Event:
        """Create a new event."""
        if self.calendar_id == "primary":
            url = "/me/calendar/events"
        else:
            url = f"/me/calendars/{self.calendar_id}/events"
        event_data = to_graph_event(event)
        
        response = self._make_request("POST", url, json=event_data)
        return from_graph_event(response)
    
    def edit(self, event_id: str, patch: dict) -> Event:
        """Update an existing event."""
        if self.calendar_id == "primary":
            url = f"/me/calendar/events/{event_id}"
        else:
            url = f"/me/calendars/{self.calendar_id}/events/{event_id}"
        
        # Convert patch to Graph format if needed
        graph_patch = self._convert_patch_to_graph(patch)
        
        response = self._make_request("PATCH", url, json=graph_patch)
        return from_graph_event(response)
    
    def delete(self, event_id: str) -> None:
        """Delete an event."""
        if self.calendar_id == "primary":
            url = f"/me/calendar/events/{event_id}"
        else:
            url = f"/me/calendars/{self.calendar_id}/events/{event_id}"
        self._make_request("DELETE", url)
    
    def search(
        self, 
        query: str, 
        start: Optional[datetime] = None, 
        end: Optional[datetime] = None
    ) -> Iterable[Event]:
        """Search for events."""
        # Use agenda with search query
        if start is None:
            from datetime import datetime, timedelta
            start = datetime.now()
        if end is None:
            end = start + timedelta(days=30)
        
        return self.agenda(start, end, query)
    
    def import_ics(self, ics_content: str, calendar_id: Optional[str] = None) -> int:
        """Import events from ICS content."""
        calendar = ICalendar.from_ical(ics_content)
        imported_count = 0
        
        for component in calendar.walk():
            if component.name == "VEVENT":
                # Convert iCalendar event to our Event model
                event = self._convert_ical_to_event(component)
                if event:
                    try:
                        self.add(event)
                        imported_count += 1
                    except Exception as e:
                        print(f"Warning: Failed to import event '{event.subject}': {e}")
        
        return imported_count
    
    def _convert_patch_to_graph(self, patch: dict) -> dict:
        """Convert patch dictionary to Graph API format."""
        graph_patch = {}
        
        # Map common fields
        field_mapping = {
            "subject": "subject",
            "body": "body",
            "location": "location",
            "start": "start",
            "end": "end",
            "all_day": "isAllDay",
            "attendees": "attendees",
            "reminders": "reminderMinutesBeforeStart"
        }
        
        for key, value in patch.items():
            if key in field_mapping:
                graph_key = field_mapping[key]
                
                if key == "body":
                    graph_patch[graph_key] = {
                        "contentType": "text",
                        "content": value
                    }
                elif key == "location":
                    graph_patch[graph_key] = {
                        "displayName": value
                    }
                elif key in ["start", "end"]:
                    if isinstance(value, datetime):
                        graph_patch[graph_key] = {
                            "dateTime": value.isoformat(),
                            "timeZone": str(value.tzinfo) if value.tzinfo else "UTC"
                        }
                elif key == "attendees":
                    graph_patch[graph_key] = [
                        {
                            "emailAddress": {"address": email},
                            "type": "required"
                        }
                        for email in value
                    ]
                else:
                    graph_patch[graph_key] = value
        
        return graph_patch
    
    def _convert_ical_to_event(self, ical_event) -> Optional[Event]:
        """Convert iCalendar event to ocalcli Event model."""
        try:
            # Extract basic fields
            subject = str(ical_event.get("summary", ""))
            description = str(ical_event.get("description", ""))
            location = str(ical_event.get("location", ""))
            
            # Parse start/end times
            start_dt = ical_event.get("dtstart")
            end_dt = ical_event.get("dtend")
            
            if not start_dt or not end_dt:
                return None
            
            # Convert to datetime objects
            if hasattr(start_dt.dt, 'date'):
                # All-day event
                start = datetime.combine(start_dt.dt, datetime.min.time())
                end = datetime.combine(end_dt.dt, datetime.min.time())
                all_day = True
            else:
                start = start_dt.dt
                end = end_dt.dt
                all_day = False
            
            # Parse attendees
            attendees = []
            for attendee in ical_event.get("attendee", []):
                if hasattr(attendee, 'params') and 'CN' in attendee.params:
                    email = attendee.params['CN']
                    attendees.append(email)
            
            # Parse recurrence (basic support)
            recurrence = None
            if rrule := ical_event.get("rrule"):
                freq = rrule.get("FREQ", [""])[0].upper()
                if freq in ["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]:
                    interval = int(rrule.get("INTERVAL", [1])[0])
                    byday = rrule.get("BYDAY", [])
                    
                    recurrence = {
                        "frequency": freq,
                        "interval": interval,
                        "days_of_week": [day.lower() for day in byday] if byday else None
                    }
            
            return Event(
                subject=subject,
                body=description,
                location=location,
                start=start,
                end=end,
                all_day=all_day,
                attendees=attendees,
                recurrence=recurrence
            )
            
        except Exception as e:
            print(f"Warning: Failed to parse iCalendar event: {e}")
            return None
    
    def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
