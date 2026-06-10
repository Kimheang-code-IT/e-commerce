from datetime import date, datetime, time, timedelta, timezone


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


def format_cambodia_report_date_dd_mmm_yyyy(when: datetime | None = None) -> str:
    """e.g. 10-Jun-2026 for Telegram Report Today header."""
    dt = when or cambodia_now()
    return dt.strftime("%d-%b-%Y")


def format_report_period_date_label(value: date | datetime | str | None) -> str:
    """Format a report period boundary for Telegram (dd-mmm-yyyy) or All."""
    if value is None:
        return "All"
    if isinstance(value, str):
        raw = value.strip()[:10]
        try:
            parsed = datetime.strptime(raw, "%Y-%m-%d")
        except ValueError:
            return raw
        return parsed.strftime("%d-%b-%Y")
    if isinstance(value, datetime):
        return value.strftime("%d-%b-%Y")
    return value.strftime("%d-%b-%Y")
