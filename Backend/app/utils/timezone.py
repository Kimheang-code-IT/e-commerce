from datetime import datetime, time, timedelta, timezone


def cambodia_now() -> datetime:
    """Returns current naive datetime in Cambodia (UTC+7)."""
    return datetime.utcnow() + timedelta(hours=7)


def cambodia_today_sales_window(
    *,
    start_hour: int = 7,
    start_minute: int = 0,
    end_hour: int = 19,
    end_minute: int = 0,
) -> tuple[datetime, datetime, datetime]:
    """Business-day window on today's Cambodia calendar date (default 7:00–19:00)."""
    now = cambodia_now()
    day = now.date()
    start = datetime.combine(day, time(start_hour, start_minute))
    end = datetime.combine(day, time(end_hour, end_minute))
    return start, end, now


def format_cambodia_report_date_label(when: datetime | None = None) -> str:
    """e.g. Wed/03/June/2026 for Telegram daily sales header."""
    dt = when or cambodia_now()
    return dt.strftime("%a/%d/%B/%Y")
