# ocalcli - Outlook Calendar Command Line Interface

A command-line interface for Microsoft Outlook/Office 365 calendars, inspired by gcalcli but built for Microsoft Graph API.

## Features

- **Calendar Management**: View, create, edit, and delete calendar events
- **Quick Day Views**: Easy access to today, yesterday, and tomorrow with `today`, `yesterday`, `tomorrow` commands
- **Natural Language**: Quick event creation with natural language parsing
- **Multiple Formats**: Rich terminal output and JSON export for scripting
- **Time Zone Support**: Automatic timezone handling with configurable defaults
- **ICS Import**: Import events from .ics files
- **Search**: Full-text search across events
- **Event Editing**: Full event editing with easy ID lookup
- **Authentication**: Secure OAuth2 device code flow with token caching

## Installation

### From Source

```bash
git clone https://github.com/insanum/ocalcli.git
cd ocalcli
pip install -e .
```

**Note for Windows users:** If you encounter installation errors, make sure you have the latest pip version:
```bash
python -m pip install --upgrade pip
```

### With pipx (recommended)

```bash
pipx install ocalcli
```

## Quick Start

### Step 1: Install ocalcli

**From Source:**
```bash
git clone https://github.com/insanum/ocalcli.git
cd ocalcli
pip install -e .
```

**With pipx (recommended):**
```bash
pipx install ocalcli
```

### Step 2: Create Azure App Registration (Required)

You need to create an Azure app registration to use ocalcli:

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Enter a name (e.g., "ocalcli")
5. Select "Accounts in any organizational directory and personal Microsoft accounts"
6. Click "Register"
7. **Copy the "Application (client) ID"** - you'll need this
8. Go to "API permissions" and add:
   - Microsoft Graph > Calendars.ReadWrite
   - Microsoft Graph > offline_access
9. Grant admin consent for your organization

### Step 3: Configure ocalcli

```bash
ocalcli configure
```

This will prompt you for:
- Azure app registration client ID (paste the one from Step 2)
- Azure tenant ID (press Enter to use "common")
- Default timezone (press Enter to use "UTC" or specify like "Europe/London")

### Step 4: Test Your Setup

**View today's calendar:**
```bash
ocalcli today
```

**Add an event:**
```bash
ocalcli add "Team Meeting" --start "2025-01-15T14:00" --end "2025-01-15T15:00"
```

**Use natural language:**
```bash
ocalcli quickadd "Tomorrow 4pm: Coffee with Ali @ Cafe Nero"
```

## Commands

### `ocalcli configure`
Configure ocalcli with your Azure app registration details.

### `ocalcli agenda [OPTIONS]`
Show calendar agenda for a date range.

**Options:**
- `--start YYYY-MM-DD`: Start date (default: today)
- `--end YYYY-MM-DD`: End date (default: +7 days)
- `--tz TIMEZONE`: Timezone override
- `--query TEXT`: Search query
- `--json`: Output as JSON

### `ocalcli today [OPTIONS]`
Show today's calendar agenda.

**Options:**
- `--tz TIMEZONE`: Timezone override
- `--query TEXT`: Search query
- `--json`: Output as JSON

### `ocalcli yesterday [OPTIONS]`
Show yesterday's calendar agenda.

**Options:**
- `--tz TIMEZONE`: Timezone override
- `--query TEXT`: Search query
- `--json`: Output as JSON

### `ocalcli tomorrow [OPTIONS]`
Show tomorrow's calendar agenda.

**Options:**
- `--tz TIMEZONE`: Timezone override
- `--query TEXT`: Search query
- `--json`: Output as JSON

### `ocalcli list-events [OPTIONS]`
List events for a specific date (alias for agenda).

**Options:**
- `--date YYYY-MM-DD`: Specific date
- `--tz TIMEZONE`: Timezone override
- `--json`: Output as JSON

### `ocalcli add SUBJECT [OPTIONS]`
Add a new event to the calendar.

**Options:**
- `--start DATETIME`: Start time (required)
- `--end DATETIME`: End time (required)
- `--location TEXT`: Event location
- `--body TEXT`: Event description
- `--attendee EMAIL`: Attendee email (can be used multiple times)
- `--reminder MINUTES`: Reminder minutes before start
- `--all-day`: All-day event
- `--recurrence RRULE`: Recurrence rule
- `--tz TIMEZONE`: Timezone override

### `ocalcli edit EVENT_ID [OPTIONS]`
Edit an existing event.

**Getting Event IDs:**
- Use `--json` flag to get full event IDs: `ocalcli today --json`
- Event IDs are shown in the table output (truncated for display)
- Copy the full ID from JSON output for editing

**Options:**
- `--subject TEXT`: New subject
- `--start DATETIME`: New start time
- `--end DATETIME`: New end time
- `--location TEXT`: New location
- `--body TEXT`: New description
- `--attendee EMAIL`: New attendees
- `--reminder MINUTES`: New reminder minutes
- `--tz TIMEZONE`: Timezone override

### `ocalcli delete EVENT_ID [OPTIONS]`
Delete an event.

**Options:**
- `-y, --yes`: Skip confirmation

### `ocalcli search QUERY [OPTIONS]`
Search for events.

**Options:**
- `--start YYYY-MM-DD`: Start date filter
- `--end YYYY-MM-DD`: End date filter
- `--tz TIMEZONE`: Timezone override
- `--json`: Output as JSON

### `ocalcli import-ics FILE_PATH [OPTIONS]`
Import events from an ICS file.

**Options:**
- `--calendar CALENDAR_ID`: Target calendar ID

### `ocalcli quickadd TEXT [OPTIONS]`
Add an event using natural language.

**Options:**
- `--tz TIMEZONE`: Timezone override

**Examples:**
- `"Tomorrow 4pm: Coffee with Ali @ Cafe Nero"`
- `"Monday 9am: Standup"`
- `"Next Friday 2pm: Project review"`

## Authentication

ocalcli requires an Azure app registration to access your Microsoft calendar. This is a one-time setup that takes just a few minutes.

### Creating an Azure App Registration (Required)

You need to create an Azure app registration to use ocalcli:

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Enter a name (e.g., "ocalcli")
5. Select "Accounts in any organizational directory and personal Microsoft accounts"
6. Click "Register"
7. Note the "Application (client) ID"
8. Go to "API permissions" and add:
   - Microsoft Graph > Calendars.ReadWrite
   - Microsoft Graph > offline_access
9. Grant admin consent for your organization

## Configuration

Configuration is stored in:
- **Windows**: `%APPDATA%\\ocalcli\\config.toml`
- **macOS**: `~/Library/Application Support/ocalcli/config.toml`
- **Linux**: `~/.config/ocalcli/config.toml`

Token cache is stored in the same directory as `msal_token_cache.bin`.

### Environment Variables

- `OCALCLI_CLIENT_ID`: Azure app registration client ID
- `OCALCLI_TENANT`: Azure tenant ID
- `OCALCLI_TZ`: Default timezone
- `OCALCLI_CALENDAR_ID`: Default calendar ID

## Time Zone Handling

- Defaults to your system timezone
- Can be overridden with `--tz` flag or `OCALCLI_TZ` environment variable
- Supports all standard timezone names (e.g., "Europe/Dublin", "America/New_York")
- Naive datetimes are automatically localized to the specified timezone

## Recurrence Support

Currently supports a subset of RRULE patterns:
- `FREQ=DAILY` with `INTERVAL`
- `FREQ=WEEKLY` with `INTERVAL` and `BYDAY`

Example:
```bash
ocalcli add "Daily Standup" --start "2025-01-15T09:00" --end "2025-01-15T09:30" --recurrence "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"
```

## Output Format

### Table Output
All agenda commands show events in a rich table format with:
- **ID**: Event ID (truncated for display, use `--json` for full ID)
- **Start**: Event start time
- **End**: Event end time  
- **Subject**: Event title
- **Location**: Event location

### JSON Output
All commands support `--json` flag for machine-readable output:

```bash
ocalcli agenda --json | jq '.[0].subject'
```

**Getting Full Event IDs for Editing:**
```bash
# Get full event IDs
ocalcli today --json

# Copy the full ID from the JSON output
# Then use it for editing
ocalcli edit "FULL_EVENT_ID" --subject "New Title"
```

## Examples

### View today's agenda
```bash
ocalcli today
```

### View yesterday's agenda
```bash
ocalcli yesterday
```

### View tomorrow's agenda
```bash
ocalcli tomorrow
```

### View specific date range
```bash
ocalcli agenda --start 2025-01-15 --end 2025-01-17
```

### Add a meeting with attendees
```bash
ocalcli add "Project Review" \
  --start "2025-01-15T14:00" \
  --end "2025-01-15T15:00" \
  --location "Conference Room A" \
  --attendee "alice@company.com" \
  --attendee "bob@company.com" \
  --body "Quarterly project review meeting"
```

### Edit an event (get ID first)
```bash
# Get event ID
ocalcli today --json

# Edit the event
ocalcli edit "EVENT_ID" --subject "Updated Meeting Title"
```

### Search for meetings
```bash
ocalcli search "project review"
```

### Quick add with natural language
```bash
ocalcli quickadd "Tomorrow 2pm: Client call @ Office"
```

### Import from ICS file
```bash
ocalcli import-ics events.ics
```

## Troubleshooting

### Common Issues

**"command not found" on Windows:**
- Make sure you're in the virtual environment: `venv\Scripts\activate`
- Or run directly: `venv\Scripts\ocalcli`

**Authentication errors:**
- Make sure you created an Azure app registration with correct permissions
- Try running `ocalcli configure` again
- Check that your client ID is correct

**"Id is malformed" error:**
- This was fixed in recent updates - make sure you have the latest version

**Timezone issues:**
- Set your timezone explicitly: `ocalcli configure` and specify your timezone
- Use `--tz` flag to override: `ocalcli today --tz "Europe/London"`

**Empty results for specific dates:**
- Use the helper commands: `ocalcli today`, `ocalcli yesterday`, `ocalcli tomorrow`
- For custom dates, use: `ocalcli agenda --start 2025-01-15 --end 2025-01-15`

**Getting event IDs for editing:**
- Use `--json` flag: `ocalcli today --json`
- Event IDs are shown in table output (truncated)
- Copy the full ID from JSON output

## Development

### Setup
```bash
git clone https://github.com/insanum/ocalcli.git
cd ocalcli
pip install -e ".[dev]"
```

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black ocalcli tests
ruff check ocalcli tests
```

## Roadmap

- [x] Quick day views (today, yesterday, tomorrow)
- [x] Event editing with ID lookup
- [x] Rich table output with event IDs
- [x] Comprehensive troubleshooting guide
- [ ] Google Calendar provider support
- [ ] Export to ICS
- [ ] Busy/free time lookup
- [ ] Attendee response tracking
- [ ] Enhanced recurrence support
- [ ] Calendar sharing

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.

## Acknowledgments

Inspired by [gcalcli](https://github.com/insanum/gcalcli) - a Google Calendar CLI tool.