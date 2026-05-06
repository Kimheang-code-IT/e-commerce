from datetime import datetime, timedelta, timezone

def cambodia_now() -> datetime:
    """Returns current naive datetime in Cambodia (UTC+7)."""
    # Get current UTC time, then add 7 hours
    return datetime.utcnow() + timedelta(hours=7)
