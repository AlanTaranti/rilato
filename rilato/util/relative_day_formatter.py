from datetime import datetime, timezone

# Constants
THREE_DAYS = 60 * 60 * 24 * 3
MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR
MONTH = 30 * DAY
YEAR = 365 * DAY


# Simple implementation of humanize functions
def naturaltime(delta):
    """Convert a timedelta to a human-readable string."""
    seconds = delta.total_seconds()

    if seconds < 0:
        # Future time
        seconds = abs(seconds)
        if seconds < MINUTE:
            return f"in {int(seconds)} seconds"
        elif seconds < HOUR:
            return f"in {int(seconds / MINUTE)} minutes"
        elif seconds < DAY:
            return f"in {int(seconds / HOUR)} hours"
        elif seconds < 2 * DAY:
            return "tomorrow"
        elif seconds < 7 * DAY:
            return f"in {int(seconds / DAY)} days"
        else:
            # For future dates more than 7 days away, we can't use dt
            # since it's not available in this scope
            return "in the future"
    else:
        # Past time
        if seconds < MINUTE:
            return f"{int(seconds)} seconds ago"
        elif seconds < HOUR:
            return f"{int(seconds / MINUTE)} minutes ago"
        elif seconds < DAY:
            return f"{int(seconds / HOUR)} hours ago"
        elif seconds < 2 * DAY:
            return "yesterday"
        elif seconds < 7 * DAY:
            return f"{int(seconds / DAY)} days ago"
        else:
            # For past dates more than 7 days ago, we can't use dt
            # since it's not available in this scope
            return "a long time ago"


def naturaldate(dt):
    """Convert a datetime to a human-readable string."""
    now = datetime.now(timezone.utc)
    delta = now - dt
    seconds = delta.total_seconds()

    if seconds < DAY:
        return "today"
    elif seconds < 2 * DAY:
        return "yesterday"
    elif seconds < 7 * DAY:
        return f"{int(seconds / DAY)} days ago"
    else:
        return dt.strftime("%b %d, %Y")


def humanize_datetime(dt):
    """Format a datetime in a human-readable way."""
    delta = datetime.now(timezone.utc) - dt
    if delta.total_seconds() <= THREE_DAYS:
        return naturaltime(delta)
    else:
        return naturaldate(dt)
