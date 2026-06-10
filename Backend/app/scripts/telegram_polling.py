"""
Long-polling Telegram bot (reports + menus). Run as Docker service `telegram-bot`.

Requires: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_REPORT_ENABLED=true for reports.
Checkout notifications use Celery + TELEGRAM_NOTIFY_ENABLED (separate from this process).
"""
from __future__ import annotations

import asyncio
import logging

import httpx

from app.core.config import settings
from app.services.telegram_auth import (
    telegram_bot_configured,
    telegram_reports_enabled,
)
from app.services.telegram_command_service import telegram_command_service

logging.basicConfig(
    level=getattr(logging, (settings.log_level or "INFO").upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("telegram_polling")


async def _telegram_api(client: httpx.AsyncClient, method: str, payload: dict | None = None) -> dict:
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"
    response = await client.post(url, json=payload or {})
    data = response.json()
    if not data.get("ok"):
        logger.error("Telegram API %s failed: %s", method, data)
    return data


async def prepare_bot(client: httpx.AsyncClient) -> None:
    """Ensure polling mode (no webhook) and register command menu."""
    info = await _telegram_api(client, "getWebhookInfo")
    if info.get("ok") and (info.get("result") or {}).get("url"):
        logger.warning("Webhook was set; clearing once so polling can receive messages.")
        await _telegram_api(client, "deleteWebhook", {"drop_pending_updates": False})
    if not telegram_reports_enabled():
        logger.warning(
            "TELEGRAM_REPORT_ENABLED=false — /start works; report commands disabled "
            "(checkout notify uses Celery if TELEGRAM_NOTIFY_ENABLED=true)"
        )

    commands = [
        {"command": "start", "description": "Main menu"},
        {"command": "product_report", "description": "Product report"},
        {"command": "category", "description": "Category report"},
        {"command": "payment", "description": "Payment report"},
        {"command": "reward", "description": "Reward report"},
        {"command": "commission", "description": "Commission report"},
        {"command": "help", "description": "Help"},
    ]
    await _telegram_api(client, "setMyCommands", {"commands": commands})
    logger.info("Telegram command menu registered")


async def poll_telegram() -> None:
    if not telegram_bot_configured():
        logger.error("TELEGRAM_BOT_TOKEN missing — exit (disable telegram-bot service or set token)")
        raise SystemExit(1)

    chat = (settings.telegram_chat_id or "").strip()
    if not chat:
        logger.error("TELEGRAM_CHAT_ID missing — set your group/user id in Backend/.env")
        raise SystemExit(1)

    logger.info(
        "Telegram polling started (chat_id=%s, reports=%s, notify=%s)",
        chat,
        telegram_reports_enabled(),
        settings.telegram_notify_enabled,
    )

    offset = 0
    base_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}"

    async with httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=10.0)) as client:
        await prepare_bot(client)

        while True:
            try:
                response = await client.get(
                    f"{base_url}/getUpdates",
                    params={
                        "offset": offset,
                        "timeout": 30,
                        "allowed_updates": ["message", "callback_query"],
                    },
                )
                if response.status_code != 200:
                    logger.error("getUpdates HTTP %s: %s", response.status_code, response.text[:500])
                    await asyncio.sleep(5)
                    continue

                data = response.json()
                if not data.get("ok"):
                    logger.error("getUpdates error: %s", data)
                    await asyncio.sleep(5)
                    continue

                for update in data.get("result", []):
                    try:
                        await telegram_command_service.handle_update(update)
                    except Exception as exc:
                        logger.exception("handle_update failed: %s", exc)
                    offset = int(update.get("update_id", 0)) + 1

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("Polling loop error: %s", exc)
                await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(poll_telegram())
    except SystemExit:
        raise
    except KeyboardInterrupt:
        logger.info("Telegram bot stopped.")
