"""Exception classes for ocalcli."""


class EventNotFoundError(Exception):
    """Raised when an event is not found."""
    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class APIError(Exception):
    """Raised when API calls fail."""
    pass