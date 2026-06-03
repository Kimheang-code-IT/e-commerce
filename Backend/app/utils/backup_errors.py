"""Short, user-friendly backup error messages (for DB + Telegram)."""

from __future__ import annotations

import re


def shorten_backup_error(exc: BaseException | str, *, max_len: int = 480) -> str:
    """Turn API/DB exceptions into a short message safe for VARCHAR(500) and Telegram."""
    msg = str(exc) if not isinstance(exc, str) else exc

    if "StringDataRightTruncation" in msg:
        return "Backup log could not be saved (message too long). Retry in 1–2 minutes."

    if (
        "429" in msg
        or "RATE_LIMIT_EXCEEDED" in msg
        or "Quota exceeded" in msg
        or "Write requests per minute" in msg
    ):
        return (
            "Google Sheets rate limit (too many writes per minute). "
            "Wait 1–2 minutes, then tap Backup again."
        )

    http = re.search(r"HttpError\s+(\d+)", msg)
    if http:
        code = http.group(1)
        if code == "429":
            return (
                "Google Sheets rate limit (429). "
                "Wait 1–2 minutes, then tap Backup again."
            )
        if code in ("403", "404"):
            return f"Google Sheets access error ({code}). Check sheet ID and sharing."
        return f"Google Sheets API error ({code})."

    if len(msg) > max_len:
        return msg[: max_len - 3] + "..."
    return msg
