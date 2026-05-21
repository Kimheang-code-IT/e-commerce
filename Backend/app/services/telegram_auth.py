"""Telegram bot authorization and feature flags."""

from __future__ import annotations

from app.core.config import settings


def telegram_bot_configured() -> bool:
    return bool((settings.telegram_bot_token or "").strip())


def telegram_reports_enabled() -> bool:
    return bool(settings.telegram_report_enabled)


def telegram_notify_enabled() -> bool:
    return bool(settings.telegram_notify_enabled and (settings.telegram_chat_id or "").strip())


def normalize_chat_id(chat_id: str | int | None) -> str:
    if chat_id is None:
        return ""
    return str(chat_id).strip()


def is_authorized_chat(chat_id: str | int | None) -> bool:
    """Only the configured TELEGRAM_CHAT_ID may use report commands."""
    configured = normalize_chat_id(settings.telegram_chat_id)
    if not configured:
        return False
    return normalize_chat_id(chat_id) == configured
