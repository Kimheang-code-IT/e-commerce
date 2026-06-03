"""Telegram alerts: low stock and scheduled backup results."""

from __future__ import annotations

import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Product
from app.utils.backup_errors import shorten_backup_error
from app.utils.timezone import cambodia_now

logger = logging.getLogger(__name__)


def get_low_stock_products(db: Session) -> list[Product]:
    threshold = max(0, int(settings.LOW_STOCK_THRESHOLD))
    return list(
        db.scalars(
            select(Product)
            .where(
                Product.status == "active",
                Product.in_stock < threshold,
            )
            .order_by(Product.in_stock.asc(), Product.name.asc())
        ).all()
    )


def format_low_stock_message(products: list[Product]) -> str:
    threshold = max(0, int(settings.LOW_STOCK_THRESHOLD))
    lines = [
        "⚠️ <b>Low Stock Alert</b>",
        f"Products with stock &lt; {threshold} — please add stock:",
        "",
    ]
    for i, p in enumerate(products, 1):
        lines.append(f"{i}. {p.name}\n   Stock left: <b>{int(p.in_stock or 0)}</b>")
    lines.append("")
    lines.append(f"Checked: {cambodia_now().strftime('%Y-%m-%d %H:%M')} (Cambodia time)")
    return "\n".join(lines)


def format_backup_success_message(results: list[dict]) -> str:
    total_rows = sum(int(r.get("total_rows") or r.get("new_rows") or 0) for r in results)
    lines = [
        "✅ <b>Google Sheets Backup Success</b>",
        f"Time: {cambodia_now().strftime('%Y-%m-%d %H:%M')} (Asia/Phnom_Penh)",
        f"Scheduled: daily at {settings.google_backup_time}",
        "",
        f"Tables synced: {len(results)} | Total rows: {total_rows}",
        "<i>Each tab has header, filters, and banded rows.</i>",
        "",
    ]
    for r in results:
        status = r.get("status", "ok")
        sheet = r.get("sheet_name", r.get("backup_name", "?"))
        rows = int(r.get("total_rows") or r.get("new_rows") or 0)
        icon = "✅" if status == "success" else "⚠️"
        lines.append(f"{icon} {sheet}: {rows} rows")
    return "\n".join(lines)


def _escape_telegram_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_backup_partial_message(results: list[dict]) -> str:
    ok = [r for r in results if r.get("status") == "success"]
    bad = [r for r in results if r.get("status") != "success"]
    lines = [
        "⚠️ <b>Google Sheets Backup — Partial</b>",
        f"Time: {cambodia_now().strftime('%Y-%m-%d %H:%M')} (Asia/Phnom_Penh)",
        "",
        f"✅ Synced: {len(ok)} tab(s)",
        f"❌ Failed: {len(bad)} tab(s)",
        "",
    ]
    for r in ok:
        sheet = r.get("sheet_name", "?")
        rows = int(r.get("total_rows") or r.get("new_rows") or 0)
        lines.append(f"✅ {sheet}: {rows} rows")
    lines.append("")
    for r in bad:
        sheet = r.get("sheet_name", "?")
        err = _escape_telegram_html(shorten_backup_error(r.get("error", "unknown")))
        lines.append(f"❌ {sheet}: {err}")
    lines.append("")
    lines.append("<i>Tip: wait 1–2 minutes before running backup again.</i>")
    return "\n".join(lines)


def format_backup_failure_message(error: str) -> str:
    safe_error = _escape_telegram_html(shorten_backup_error(error))
    return (
        "❌ <b>Google Sheets Backup Failed</b>\n"
        f"Time: {cambodia_now().strftime('%Y-%m-%d %H:%M')} (Asia/Phnom_Penh)\n"
        f"Error: {safe_error}"
    )


def run_google_backup_with_notify(db: Session) -> dict:
    from app.services.backup_service import backup_service
    from app.services.telegram_service import telegram_service
    from app.utils.async_run import run_coro

    if not settings.google_backup_enabled or not settings.google_sheet_id:
        return {"status": "skipped", "reason": "backup_disabled"}

    chat_id = (settings.telegram_chat_id or "").strip()
    notify = settings.TELEGRAM_BACKUP_ALERT_ENABLED and bool(chat_id)

    try:
        results = backup_service.backup_all(db)
        errors = [r for r in results if r.get("status") != "success"]
        if notify:
            if errors:
                ok_count = len(results) - len(errors)
                msg = (
                    format_backup_partial_message(results)
                    if ok_count > 0
                    else format_backup_failure_message(
                        "; ".join(
                            f"{r.get('sheet_name')}: {r.get('error', r.get('status'))}"
                            for r in errors
                        )
                    )
                )
            else:
                msg = format_backup_success_message(results)
            run_coro(telegram_service.send_message(chat_id, msg))
        return {"status": "ok" if not errors else "partial", "results": results}
    except Exception as exc:
        logger.exception("Scheduled backup failed")
        if notify:
            run_coro(
                telegram_service.send_message(
                    chat_id, format_backup_failure_message(shorten_backup_error(exc))
                )
            )
        return {"status": "error", "error": str(exc)}


def run_low_stock_alert(db: Session) -> dict:
    from app.services.telegram_service import telegram_service
    from app.utils.async_run import run_coro

    if not settings.LOW_STOCK_ALERT_ENABLED:
        return {"status": "skipped", "reason": "low_stock_disabled"}
    if not settings.telegram_notify_enabled:
        return {"status": "skipped", "reason": "telegram_notify_disabled"}

    chat_id = (settings.telegram_chat_id or "").strip()
    if not chat_id:
        return {"status": "skipped", "reason": "no_chat_id"}

    products = get_low_stock_products(db)
    if not products:
        return {"status": "ok", "alerted": 0}

    msg = format_low_stock_message(products)
    run_coro(telegram_service.send_message(chat_id, msg))
    return {"status": "ok", "alerted": len(products)}
