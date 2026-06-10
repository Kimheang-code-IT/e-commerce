import logging
from datetime import timedelta

from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.repositories.report_repository import report_repo
from app.services.report_service import report_service
from app.services.telegram_auth import (
    is_authorized_chat,
    normalize_chat_id,
    telegram_bot_configured,
    telegram_reports_enabled,
)
from app.services.telegram_menu_service import telegram_menu_service
from app.services.telegram_service import telegram_service
from app.utils.timezone import cambodia_now

logger = logging.getLogger(__name__)

# Simple in-memory state store: chat_id -> state_name
user_states = {}
# Filter context for list → period → report (product_id, category_id, payment_method, user_id)
user_report_context: dict[str, dict] = {}

class TelegramCommandService:
    async def _menu_reply(
        self,
        chat_id: str,
        text: str,
        reply_markup: dict | None = None,
    ) -> None:
        """Reply with a new message only (no editMessage / deleteMessage)."""
        await telegram_service.send_message(chat_id, text, reply_markup)

    def get_backup_info_message(self) -> str:
        return (
            "📊 <b>Google Sheets Backup</b>\n\n"
            "Exports <b>all data</b> from each table to your spreadsheet:\n"
            "Products, Categories, Invoices, Invoice Details, Deliveries, Users, Roles, "
            "Suppliers, Supplier Products, Refunds.\n\n"
            "Each tab is formatted as a real table (header row, filters, banded rows).\n"
            "Tap <b>📊 Backup Google Sheets</b> or send /backup to run now."
        )

    async def trigger_google_backup(self, chat_id: str) -> None:
        if not settings.google_backup_enabled or not settings.google_sheet_id:
            await telegram_service.send_message(
                chat_id,
                "⚠️ Google backup is not configured.\n"
                "Set <code>GOOGLE_BACKUP_ENABLED=true</code> and <code>GOOGLE_SHEET_ID</code> in Backend/.env.",
            )
            return
        if not settings.google_service_account_file:
            await telegram_service.send_message(chat_id, "⚠️ <code>GOOGLE_SERVICE_ACCOUNT_FILE</code> is missing.")
            return

        await telegram_service.send_message(
            chat_id,
            "⏳ <b>Backing up all tables to Google Sheets…</b>\nThis may take a minute.",
        )
        db = SessionLocal()
        try:
            from app.services.alert_service import run_google_backup_with_notify

            run_google_backup_with_notify(db)
        except Exception as exc:
            logger.exception("Telegram-triggered backup failed: %s", exc)
            from app.utils.backup_errors import shorten_backup_error

            err = shorten_backup_error(exc).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            await telegram_service.send_message(
                chat_id,
                f"❌ Backup failed: {err[:400]}",
            )
        finally:
            db.close()

    def get_date_range(self, period: str):
        today = cambodia_now().date()
        if period == "today":
            return today, today
        elif period == "3days":
            return today - timedelta(days=2), today
        elif period == "7days":
            return today - timedelta(days=6), today
        elif period == "1month":
            return today - timedelta(days=30), today
        elif period == "all":
            return None, None
        return None, None

    async def handle_update(self, update: dict):
        if not telegram_bot_configured():
            return
        if not isinstance(update, dict):
            return

        callback_query = update.get("callback_query")
        if isinstance(callback_query, dict):
            await self.handle_callback(callback_query)
            return

        message = update.get("message")
        if isinstance(message, dict):
            await self.handle_message(message)

    async def _reply_reports_disabled(self, chat_id: str) -> None:
        await telegram_service.send_message(
            chat_id,
            "📴 <b>Report commands are disabled</b> on this server.\n"
            "Checkout notifications may still be sent if enabled.\n"
            "Set <code>TELEGRAM_REPORT_ENABLED=true</code> in Backend/.env and restart.",
        )

    async def handle_message(self, message: dict):
        if not isinstance(message, dict):
            return

        chat = message.get("chat") or {}
        raw_chat_id = chat.get("id")
        if raw_chat_id is None:
            return

        chat_id = normalize_chat_id(raw_chat_id)
        text = (message.get("text") or message.get("caption") or "").strip()

        if not is_authorized_chat(chat_id):
            await telegram_service.send_message(chat_id, "🚫 Unauthorized.")
            return

        # If user is waiting for custom range, parse text first.
        # This avoids sending fallback menu before processing the range.
        state = user_states.get(chat_id)
        if state and state.startswith("waiting_"):
            if not telegram_reports_enabled():
                user_states.pop(chat_id, None)
                await self._reply_reports_disabled(chat_id)
                return
            if not text:
                await telegram_service.send_message(
                    chat_id,
                    "⚠️ Please send date range in this format: <code>2026-05-01 2026-05-08</code>"
                )
                return
            await self.process_custom_range(chat_id, text, state)
            return

        if not text:
            return

        # Check for /start or /help
        if text.startswith("/"):
            command = text.split("@")[0] # handle /start@bot_name

            if command == "/start":
                msg = "📊 <b>Shop Report Bot</b>\n\n"
                if telegram_reports_enabled():
                    msg += "Please choose report type from the menu below:"
                    await telegram_service.send_reply_keyboard(
                        chat_id,
                        msg,
                        telegram_menu_service.get_reply_keyboard(),
                    )
                else:
                    msg += "Reports are off. Checkout alerts use <code>TELEGRAM_NOTIFY_ENABLED</code>."
                    await telegram_service.send_message(chat_id, msg)
                user_states.pop(chat_id, None)
                user_report_context.pop(chat_id, None)
                return
            elif command in ("/backup", "/help"):
                await self.trigger_google_backup(chat_id)
                user_states.pop(chat_id, None)
                return

            elif command in {
                "/category",
                "/product",
                "/payment",
                "/commission",
                "/product_report",
            }:
                if not telegram_reports_enabled():
                    await self._reply_reports_disabled(chat_id)
                    return
                if command == "/category":
                    await self.prompt_category_list(chat_id)
                elif command == "/product":
                    await self.prompt_product_list(chat_id)
                elif command == "/payment":
                    await self.prompt_payment_list(chat_id)
                elif command == "/commission":
                    await self.prompt_commission_list(chat_id)
                elif command == "/product_report":
                    await self.prompt_product_list(chat_id)
                return
            else:
                await telegram_service.send_message(
                    chat_id,
                    "❓ Unknown command. Send /start or /backup.",
                )
                return

        lower_text = text.lower()
        if "backup" in lower_text or "google sheet" in lower_text:
            await self.trigger_google_backup(chat_id)
            return

        if not telegram_reports_enabled():
            await self._reply_reports_disabled(chat_id)
            return

        if "product report" in lower_text or text.strip() in {"💰 Summary", "Summary"}:
            await self.prompt_product_list(chat_id)
            return
        elif "category" in lower_text:
            await self.prompt_category_list(chat_id)
            return
        elif "payment" in lower_text:
            await self.prompt_payment_list(chat_id)
            return
        elif "commission" in lower_text:
            await self.prompt_commission_list(chat_id)
            return
        # Fallback: Restore keyboard for any unknown input
        await telegram_service.send_message(
            chat_id, 
            "❓ I didn't recognize that. Please use the menu below:", 
            telegram_menu_service.get_reply_keyboard()
        )

    async def handle_callback(self, query: dict):
        if not isinstance(query, dict):
            return

        callback_query_id = query.get("id")
        data = query.get("data", "")
        message = query.get("message") or {}
        chat = message.get("chat") or {}
        raw_chat_id = chat.get("id")
        if raw_chat_id is None:
            if callback_query_id:
                await telegram_service.answer_callback(callback_query_id)
            return

        chat_id = normalize_chat_id(raw_chat_id)

        if not is_authorized_chat(chat_id):
            if callback_query_id:
                await telegram_service.answer_callback(callback_query_id, "Unauthorized")
            return

        if callback_query_id:
            await telegram_service.answer_callback(callback_query_id)

        if data == "main_google_backup":
            await self.trigger_google_backup(chat_id)
            return

        if not telegram_reports_enabled():
            await telegram_service.send_message(chat_id, "📴 Report commands are disabled on this server.")
            return

        # Main Menu Actions
        if data == "back_main":
            await telegram_service.send_reply_keyboard(
                chat_id,
                "📊 <b>Shop Report Bot</b>\nMain menu restored. Please use the buttons below.",
                telegram_menu_service.get_reply_keyboard(),
            )
            user_states.pop(chat_id, None)
            user_report_context.pop(chat_id, None)
            return

        if data.startswith("main_"):
            type_prefix = data.replace("main_", "")
            if type_prefix == "google_backup":
                await self.trigger_google_backup(chat_id)
                return
            if type_prefix == "product_report":
                await self.prompt_product_list(chat_id)
                return
            if type_prefix == "category_price":
                await self.prompt_category_list(chat_id)
                return
            if type_prefix == "payment_price":
                await self.prompt_payment_list(chat_id)
                return
            if type_prefix == "commission_user":
                await self.prompt_commission_list(chat_id)
                return

        if data.startswith("prod_select_"):
            product_key = data.replace("prod_select_", "")
            if product_key == "all":
                user_report_context[chat_id] = {}
            else:
                user_report_context[chat_id] = {"product_id": int(product_key)}
            await self._menu_reply(
                chat_id,
                "📅 <b>Select Period</b>\nChoose a period for this product report:",
                telegram_menu_service.get_date_menu("prod_detail"),
            )
            return

        if data.startswith("cat_select_"):
            category_key = data.replace("cat_select_", "")
            if category_key == "all":
                user_report_context[chat_id] = {}
            else:
                user_report_context[chat_id] = {"category_id": int(category_key)}
            await self._menu_reply(
                chat_id,
                "📅 <b>Select Period</b>\nChoose a period for this category report:",
                telegram_menu_service.get_date_menu("cat_detail"),
            )
            return

        if data.startswith("pay_select_"):
            method_name = data.replace("pay_select_", "")
            if method_name == "all":
                user_report_context[chat_id] = {}
            else:
                user_report_context[chat_id] = {"payment_method": method_name}
            await self._menu_reply(
                chat_id,
                "📅 <b>Select Period</b>\nChoose a period for this payment report:",
                telegram_menu_service.get_date_menu("pay_detail"),
            )
            return

        if data.startswith("usr_select_"):
            user_key = data.replace("usr_select_", "")
            if user_key == "all":
                user_report_context[chat_id] = {}
            else:
                user_report_context[chat_id] = {"user_id": int(user_key)}
            await self._menu_reply(
                chat_id,
                "📅 <b>Select Period</b>\nChoose a period for this commission report:",
                telegram_menu_service.get_date_menu("usr_detail"),
            )
            return

        # Date Pattern Actions
        if "_today" in data or "_3days" in data or "_7days" in data or "_1month" in data or "_all" in data or "_custom" in data:
            await self.process_date_callback(chat_id, data)

    def _detail_report_types(self) -> set[str]:
        return {"prod_detail", "cat_detail", "pay_detail", "usr_detail"}

    def _menu_prefix_for_report(self, report_type: str) -> str:
        return {
            "prod_detail": "product_report",
            "cat_detail": "category_price",
            "pay_detail": "payment_price",
            "usr_detail": "commission_user",
        }.get(report_type, report_type)

    async def process_date_callback(self, chat_id: str, data: str):
        parts = data.split("_")
        period = parts[-1]
        report_type = "_".join(parts[:-1])

        if report_type in self._detail_report_types() and chat_id not in user_report_context:
            await telegram_service.send_message(chat_id, "⚠️ Session expired. Please start over.")
            return

        if period == "custom":
            user_states[chat_id] = f"waiting_{report_type}_range"
            await telegram_service.send_message(
                chat_id,
                "📅 <b>Custom Date Range</b>\nPlease input: <code>YYYY-MM-DD YYYY-MM-DD</code>\n"
                "Example: <code>2026-05-01 2026-05-08</code>",
            )
            return

        start, end = self.get_date_range(period)
        label = period.replace("days", " Days").capitalize() if period != "all" else "All Time"
        await self.run_and_send_report(chat_id, report_type, start, end, label)

    async def process_custom_range(self, chat_id: str, text: str, state: str):
        try:
            parts = text.split()
            if len(parts) != 2: raise ValueError()
            start, end = parts[0], parts[1]
            # Basic validation
            if len(start) != 10 or len(end) != 10: raise ValueError()
            
            report_type = state.replace("waiting_", "").replace("_range", "")
            user_states.pop(chat_id, None)
            await self.run_and_send_report(chat_id, report_type, start, end, f"{start} to {end}")
        except:
            await telegram_service.send_message(chat_id, "❌ Invalid date range.\nPlease use this format: <code>2026-05-01 2026-05-08</code>")

    async def _send_chunked_report(self, chat_id: str, report_type: str, messages: list[str]) -> None:
        for index, msg in enumerate(messages):
            reply_markup = (
                telegram_menu_service.get_post_report_menu(report_type)
                if index == len(messages) - 1
                else None
            )
            await telegram_service.send_message(chat_id, msg, reply_markup)

    async def run_and_send_report(self, chat_id: str, report_type: str, start, end, label: str):
        db = SessionLocal()
        ctx = user_report_context.get(chat_id, {})
        menu_prefix = self._menu_prefix_for_report(report_type)
        try:
            if report_type == "prod_detail":
                messages = report_service.format_product_report_messages(
                    db,
                    start,
                    end,
                    product_id=ctx.get("product_id"),
                )
                await self._send_chunked_report(chat_id, menu_prefix, messages)
                return
            if report_type == "cat_detail":
                messages = report_service.format_category_report_messages(
                    db,
                    start,
                    end,
                    category_id=ctx.get("category_id"),
                )
                await self._send_chunked_report(chat_id, menu_prefix, messages)
                return
            if report_type == "pay_detail":
                messages = report_service.format_payment_report_messages(
                    db,
                    start,
                    end,
                    payment_method=ctx.get("payment_method"),
                )
                await self._send_chunked_report(chat_id, menu_prefix, messages)
                return
            if report_type == "usr_detail":
                messages = report_service.format_commission_report_messages(
                    db,
                    start,
                    end,
                    user_id=ctx.get("user_id"),
                )
                await self._send_chunked_report(chat_id, menu_prefix, messages)
                return

            msg = ""
            if report_type == "summary_price":
                msg = report_service.format_summary_price(db, start, end, label)

            if msg:
                await telegram_service.send_message(
                    chat_id, msg, telegram_menu_service.get_post_report_menu(menu_prefix)
                )
        except Exception as e:
            logger.error(f"Report error: {e}")
            await telegram_service.send_message(chat_id, "❌ Error generating report.")
        finally:
            db.close()

    async def prompt_product_list(self, chat_id: str):
        with next(get_db()) as db:
            products = report_repo.get_all_products(db)
            await self._menu_reply(
                chat_id,
                "📦 <b>Product Report</b>\nSelect a product:",
                telegram_menu_service.get_product_list_menu(products),
            )

    async def prompt_category_list(self, chat_id: str):
        with next(get_db()) as db:
            categories = report_repo.get_all_categories(db)
            await self._menu_reply(
                chat_id,
                "📁 <b>Category Report</b>\nSelect a category:",
                telegram_menu_service.get_category_list_menu(categories),
            )

    async def prompt_payment_list(self, chat_id: str):
        with next(get_db()) as db:
            methods = report_repo.get_all_payment_methods(db)
            await self._menu_reply(
                chat_id,
                "💳 <b>Payment Report</b>\nSelect a payment method:",
                telegram_menu_service.get_payment_list_menu(methods),
            )

    async def prompt_commission_list(self, chat_id: str):
        with next(get_db()) as db:
            users = report_repo.get_all_users(db)
            await self._menu_reply(
                chat_id,
                "👤 <b>Commission Report</b>\nSelect a seller:",
                telegram_menu_service.get_user_list_menu(users),
            )

telegram_command_service = TelegramCommandService()
