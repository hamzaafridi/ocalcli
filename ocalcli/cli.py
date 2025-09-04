"""Command-line interface for ocalcli."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from .auth.outlook_auth import OutlookAuth
from .config import Config
from .models import Event, Reminder, Recurrence
from .providers.outlook import OutlookProvider
from .providers.base import APIError, AuthenticationError, EventNotFoundError
from .quickadd import parse_quickadd
from .timeutils import parse_datetime, parse_date_range, get_system_timezone

app = typer.Typer(
    name="ocalcli",
    help="Outlook Calendar Command Line Interface",
    no_args_is_help=True
)
console = Console()


def get_provider() -> OutlookProvider:
    """Get configured calendar provider."""
    config = Config()
    
    if not config.is_configured():
        console.print("[red]Error: Not configured. Run 'ocalcli configure' first.[/red]")
        raise typer.Exit(1)
    
    try:
        auth = OutlookAuth(
            client_id=config.client_id,
            tenant=config.tenant
        )
        return OutlookProvider(auth, config.calendar_id)
    except Exception as e:
        console.print(f"[red]Error: Failed to initialize provider: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def configure():
    """Configure ocalcli with Azure app registration details."""
    config = Config()
    
    console.print("[bold blue]ocalcli Configuration[/bold blue]")
    console.print()
    
    # Get client ID
    current_client_id = config.client_id
    if current_client_id:
        console.print(f"Current client ID: {current_client_id}")
        if not typer.confirm("Change client ID?"):
            client_id = current_client_id
        else:
            client_id = typer.prompt("Azure app registration client ID")
    else:
        client_id = typer.prompt(
            "Azure app registration client ID",
            default="04b07795-8ddb-461a-bbee-02f9e1bf7b46"
        )
    
    # Get tenant
    current_tenant = config.tenant
    tenant = typer.prompt(
        "Azure tenant ID (or 'organizations' for multi-tenant)",
        default=current_tenant
    )
    
    # Get timezone
    current_tz = config.timezone
    timezone = typer.prompt(
        "Default timezone",
        default=current_tz
    )
    
    # Save configuration
    config.client_id = client_id
    config.tenant = tenant
    config.timezone = timezone
    config.save_config()
    
    console.print("\n[green]Configuration saved![/green]")
    
    # Test authentication
    console.print("\nTesting authentication...")
    try:
        auth = OutlookAuth(client_id=client_id, tenant=tenant)
        token = auth.get_access_token()
        console.print("[green]Authentication successful![/green]")
    except Exception as e:
        console.print(f"[red]Authentication failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def agenda(
    start: Optional[str] = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
    end: Optional[str] = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
    tz: Optional[str] = typer.Option(None, "--tz", help="Timezone"),
    query: Optional[str] = typer.Option(None, "--query", help="Search query"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """Show calendar agenda for a date range."""
    try:
        provider = get_provider()
        config = Config()
        timezone_name = tz or config.timezone
        
        # Parse date range
        start_dt, end_dt = parse_date_range(start, end, timezone_name)
        
        # Get events
        events = list(provider.agenda(start_dt, end_dt, query))
        
        if json_output:
            # Output as JSON
            events_data = []
            for event in events:
                event_data = {
                    "id": event.id,
                    "subject": event.subject,
                    "start": event.start.isoformat() if event.start else None,
                    "end": event.end.isoformat() if event.end else None,
                    "location": event.location,
                    "all_day": event.all_day,
                    "attendees": event.attendees
                }
                events_data.append(event_data)
            
            console.print(json.dumps(events_data, indent=2))
        else:
            # Output as table
            table = Table(title="Calendar Agenda")
            table.add_column("Start", style="cyan")
            table.add_column("End", style="cyan")
            table.add_column("Subject", style="green")
            table.add_column("Location", style="yellow")
            
            for event in events:
                start_str = event.start.strftime("%Y-%m-%d %H:%M") if event.start else "N/A"
                end_str = event.end.strftime("%Y-%m-%d %H:%M") if event.end else "N/A"
                location = event.location or ""
                
                table.add_row(start_str, end_str, event.subject, location)
            
            console.print(table)
    
    except (AuthenticationError, APIError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list_events(
    date: Optional[str] = typer.Option(None, "--date", help="Date (YYYY-MM-DD)"),
    tz: Optional[str] = typer.Option(None, "--tz", help="Timezone"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """List events for a specific date (alias for agenda)."""
    # Convert single date to date range
    if date:
        start = date
        end = date
    else:
        start = None
        end = None
    
    # Call agenda with the same parameters
    agenda(start, end, tz, None, json_output)


@app.command()
def add(
    subject: str = typer.Argument(..., help="Event subject"),
    start: str = typer.Option(..., "--start", help="Start time (YYYY-MM-DDTHH:MM)"),
    end: str = typer.Option(..., "--end", help="End time (YYYY-MM-DDTHH:MM)"),
    location: Optional[str] = typer.Option(None, "--location", help="Event location"),
    body: Optional[str] = typer.Option(None, "--body", help="Event description"),
    attendee: Optional[List[str]] = typer.Option(None, "--attendee", help="Attendee email"),
    reminder: Optional[int] = typer.Option(None, "--reminder", help="Reminder minutes before start"),
    all_day: bool = typer.Option(False, "--all-day", help="All-day event"),
    recurrence: Optional[str] = typer.Option(None, "--recurrence", help="Recurrence rule (RRULE)"),
    tz: Optional[str] = typer.Option(None, "--tz", help="Timezone")
):
    """Add a new event to the calendar."""
    try:
        provider = get_provider()
        config = Config()
        timezone_name = tz or config.timezone
        
        # Parse start and end times
        start_dt = parse_datetime(start, timezone_name)
        end_dt = parse_datetime(end, timezone_name)
        
        # Create event
        event = Event(
            subject=subject,
            body=body,
            location=location,
            start=start_dt,
            end=end_dt,
            all_day=all_day,
            attendees=attendee or [],
            reminders=Reminder(minutes_before_start=reminder) if reminder else None
        )
        
        # Add recurrence if specified
        if recurrence:
            # Basic recurrence parsing (simplified)
            if "FREQ=WEEKLY" in recurrence:
                event.recurrence = Recurrence(
                    frequency="WEEKLY",
                    interval=1
                )
        
        # Create event
        created_event = provider.add(event)
        
        console.print(f"[green]Event created: {created_event.id}[/green]")
        console.print(f"Subject: {created_event.subject}")
        console.print(f"Start: {created_event.start}")
        console.print(f"End: {created_event.end}")
    
    except (AuthenticationError, APIError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def edit(
    event_id: str = typer.Argument(..., help="Event ID"),
    subject: Optional[str] = typer.Option(None, "--subject", help="New subject"),
    start: Optional[str] = typer.Option(None, "--start", help="New start time"),
    end: Optional[str] = typer.Option(None, "--end", help="New end time"),
    location: Optional[str] = typer.Option(None, "--location", help="New location"),
    body: Optional[str] = typer.Option(None, "--body", help="New description"),
    attendee: Optional[List[str]] = typer.Option(None, "--attendee", help="New attendees"),
    reminder: Optional[int] = typer.Option(None, "--reminder", help="New reminder minutes"),
    tz: Optional[str] = typer.Option(None, "--tz", help="Timezone")
):
    """Edit an existing event."""
    try:
        provider = get_provider()
        config = Config()
        timezone_name = tz or config.timezone
        
        # Build patch dictionary
        patch = {}
        
        if subject is not None:
            patch["subject"] = subject
        
        if start is not None:
            start_dt = parse_datetime(start, timezone_name)
            patch["start"] = start_dt
        
        if end is not None:
            end_dt = parse_datetime(end, timezone_name)
            patch["end"] = end_dt
        
        if location is not None:
            patch["location"] = location
        
        if body is not None:
            patch["body"] = body
        
        if attendee is not None:
            patch["attendees"] = attendee
        
        if reminder is not None:
            patch["reminders"] = Reminder(minutes_before_start=reminder)
        
        if not patch:
            console.print("[yellow]No changes specified[/yellow]")
            return
        
        # Update event
        updated_event = provider.edit(event_id, patch)
        
        console.print(f"[green]Event updated: {updated_event.id}[/green]")
        console.print(f"Subject: {updated_event.subject}")
    
    except EventNotFoundError:
        console.print(f"[red]Error: Event {event_id} not found[/red]")
        raise typer.Exit(1)
    except (AuthenticationError, APIError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def delete(
    event_id: str = typer.Argument(..., help="Event ID"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation")
):
    """Delete an event."""
    try:
        provider = get_provider()
        
        if not yes:
            # Get event details for confirmation
            try:
                event = provider.get(event_id)
                console.print(f"Event: {event.subject}")
                console.print(f"Start: {event.start}")
                console.print(f"End: {event.end}")
                console.print()
                
                if not typer.confirm("Are you sure you want to delete this event?"):
                    console.print("Cancelled")
                    return
            except EventNotFoundError:
                console.print(f"[red]Error: Event {event_id} not found[/red]")
                raise typer.Exit(1)
        
        # Delete event
        provider.delete(event_id)
        console.print(f"[green]Event {event_id} deleted[/green]")
    
    except EventNotFoundError:
        console.print(f"[red]Error: Event {event_id} not found[/red]")
        raise typer.Exit(1)
    except (AuthenticationError, APIError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    start: Optional[str] = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
    end: Optional[str] = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
    tz: Optional[str] = typer.Option(None, "--tz", help="Timezone"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """Search for events."""
    try:
        provider = get_provider()
        config = Config()
        timezone_name = tz or config.timezone
        
        # Parse date range if provided
        start_dt = None
        end_dt = None
        if start or end:
            start_dt, end_dt = parse_date_range(start, end, timezone_name)
        
        # Search events
        events = list(provider.search(query, start_dt, end_dt))
        
        if json_output:
            # Output as JSON
            events_data = []
            for event in events:
                event_data = {
                    "id": event.id,
                    "subject": event.subject,
                    "start": event.start.isoformat() if event.start else None,
                    "end": event.end.isoformat() if event.end else None,
                    "location": event.location,
                    "all_day": event.all_day,
                    "attendees": event.attendees
                }
                events_data.append(event_data)
            
            console.print(json.dumps(events_data, indent=2))
        else:
            # Output as table
            table = Table(title=f"Search Results for '{query}'")
            table.add_column("Start", style="cyan")
            table.add_column("End", style="cyan")
            table.add_column("Subject", style="green")
            table.add_column("Location", style="yellow")
            
            for event in events:
                start_str = event.start.strftime("%Y-%m-%d %H:%M") if event.start else "N/A"
                end_str = event.end.strftime("%Y-%m-%d %H:%M") if event.end else "N/A"
                location = event.location or ""
                
                table.add_row(start_str, end_str, event.subject, location)
            
            console.print(table)
    
    except (AuthenticationError, APIError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def import_ics(
    file_path: str = typer.Argument(..., help="Path to ICS file"),
    calendar_id: Optional[str] = typer.Option(None, "--calendar", help="Target calendar ID")
):
    """Import events from an ICS file."""
    try:
        provider = get_provider()
        
        # Read ICS file
        ics_path = Path(file_path)
        if not ics_path.exists():
            console.print(f"[red]Error: File {file_path} not found[/red]")
            raise typer.Exit(1)
        
        with open(ics_path, "r", encoding="utf-8") as f:
            ics_content = f.read()
        
        # Import events
        imported_count = provider.import_ics(ics_content, calendar_id)
        
        console.print(f"[green]Imported {imported_count} events[/green]")
    
    except (AuthenticationError, APIError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def quickadd(
    text: str = typer.Argument(..., help="Natural language event description"),
    tz: Optional[str] = typer.Option(None, "--tz", help="Timezone")
):
    """Add an event using natural language."""
    try:
        provider = get_provider()
        config = Config()
        timezone_name = tz or config.timezone
        
        # Parse natural language
        event = parse_quickadd(text, timezone_name)
        
        # Create event
        created_event = provider.add(event)
        
        console.print(f"[green]Event created: {created_event.id}[/green]")
        console.print(f"Subject: {created_event.subject}")
        console.print(f"Start: {created_event.start}")
        console.print(f"End: {created_event.end}")
        if created_event.location:
            console.print(f"Location: {created_event.location}")
    
    except (AuthenticationError, APIError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()