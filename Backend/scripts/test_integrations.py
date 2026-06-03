"""
Quick check: Google Sheets backup + Telegram (send + bot config).
Run in Docker:
  docker compose exec backend python scripts/test_integrations.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.alert_service import run_google_backup_with_notify
from app.services.telegram_service import telegram_service


def check_google() -> bool:
    print("--- Google Sheets ---")
    print(f"  GOOGLE_BACKUP_ENABLED: {settings.google_backup_enabled}")
    print(f"  GOOGLE_SHEET_ID set: {bool(settings.google_sheet_id)}")
    sa = Path(settings.google_service_account_file or "")
    print(f"  Service account file exists: {sa.is_file()} ({sa})")
    if not settings.google_sheet_id or not sa.is_file():
        return False
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_file(
            str(sa),
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
        meta = svc.spreadsheets().get(spreadsheetId=settings.google_sheet_id).execute()
        title = meta.get("properties", {}).get("title", "?")
        tabs = [s["properties"]["title"] for s in meta.get("sheets", [])]
        print(f"  Spreadsheet: {title}")
        print(f"  Tabs ({len(tabs)}): {', '.join(tabs[:7])}{'…' if len(tabs) > 7 else ''}")
        return True
    except Exception as exc:
        print(f"  FAIL: {exc}")
        return False


async def check_telegram_send() -> bool:
    print("--- Telegram send (API) ---")
    token = (settings.telegram_bot_token or "").strip()
    chat = (settings.telegram_chat_id or "").strip()
    print(f"  Token set: {bool(token)}")
    print(f"  Chat ID set: {bool(chat)}")
    print(f"  NOTIFY: {settings.telegram_notify_enabled}  REPORT: {settings.telegram_report_enabled}")
    if not token or not chat:
        return False
    import httpx

    async with httpx.AsyncClient() as client:
        me = await client.get(f"https://api.telegram.org/bot{token}/getMe")
        data = me.json()
        if not data.get("ok"):
            print(f"  getMe FAIL: {data}")
            return False
        print(f"  Bot: @{data['result'].get('username')}")

    res = await telegram_service.send_message(
        chat,
        "<b>Integration test</b>\nGoogle Sheets + Telegram are configured correctly.",
    )
    ok = bool(res and res.get("ok"))
    print(f"  sendMessage: {'OK' if ok else 'FAIL'}")
    return ok


def check_backup_job() -> bool:
    print("--- Full backup + Telegram alert ---")
    db = SessionLocal()
    try:
        out = run_google_backup_with_notify(db)
        print(f"  Status: {out.get('status')}")
        for row in out.get("results") or []:
            print(
                f"    {row.get('sheet_name')}: {row.get('status')} "
                f"(+{row.get('new_rows', 0)} rows)"
            )
        return out.get("status") in ("ok", "partial", "skipped")
    except Exception as exc:
        print(f"  FAIL: {exc}")
        return False
    finally:
        db.close()


def main() -> int:
    ok_google = check_google()
    ok_tg = asyncio.run(check_telegram_send())
    ok_backup = check_backup_job()
    print("--- Summary ---")
    print(f"  Google Sheets API: {'OK' if ok_google else 'FAIL'}")
    print(f"  Telegram send:     {'OK' if ok_tg else 'FAIL'}")
    print(f"  Backup job:        {'OK' if ok_backup else 'FAIL'}")
    print("  Telegram bot menus: send /start in your chat (telegram-bot container must be running, no 409 conflict)")
    return 0 if (ok_google and ok_tg and ok_backup) else 1


if __name__ == "__main__":
    raise SystemExit(main())
