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
                    await telegram_service.send_message(
                        chat_id,
                        msg,
                        telegram_menu_service.get_reply_keyboard(),
                    )
                else:
                    msg += "Reports are off. Checkout alerts use <code>TELEGRAM_NOTIFY_ENABLED</code>."
                    await telegram_service.send_message(chat_id, msg)
                user_states.pop(chat_id, None)
                return
            elif command in ("/backup", "/help"):
                await self.trigger_google_backup(chat_id)
                user_states.pop(chat_id, None)
                return

            elif command in {
                "/summary",
                "/category",
                "/product",
                "/source",
                "/payment",
                "/commission",
                "/delivery",
                "/product_report",
            }:
                if not telegram_reports_enabled():
                    await self._reply_reports_disabled(chat_id)
                    return
                if command == "/summary":
                    await telegram_service.send_message(
                        chat_id,
                        "💰 <b>Summary Price</b>\nSelect period:",
                        telegram_menu_service.get_date_menu("summary_price"),
                    )
                elif command == "/category":
                    await telegram_service.send_message(
                        chat_id,
                        "📁 <b>Price by Category</b>\nSelect period:",
                        telegram_menu_service.get_date_menu("category_price"),
                    )
                elif command == "/product":
                    with next(get_db()) as db:
                        products = report_repo.get_all_products(db)
                        await telegram_service.send_message(
                            chat_id,
                            "📦 <b>Select Product</b>\nPlease choose a product to view its sales report:",
                            telegram_menu_service.get_product_list_menu(products),
                        )
                elif command == "/source":
                    await telegram_service.send_message(
                        chat_id,
                        "📍 <b>Price by Source</b>\nSelect period:",
                        telegram_menu_service.get_date_menu("source_price"),
                    )
                elif command == "/payment":
                    await telegram_service.send_message(
                        chat_id,
                        "💳 <b>Price by Payment</b>\nSelect period:",
                        telegram_menu_service.get_date_menu("payment_price"),
                    )
                elif command == "/commission":
                    await telegram_service.send_message(
                        chat_id,
                        "👤 <b>Commission by User</b>\nSelect period:",
                        telegram_menu_service.get_date_menu("commission_user"),
                    )
                elif command == "/delivery":
                    await telegram_service.send_message(
                        chat_id,
                        "🚚 <b>Price by Delivery Type</b>\nSelect period:",
                        telegram_menu_service.get_date_menu("delivery_type"),
                    )
                elif command == "/product_report":
                    await self.send_product_report(chat_id)
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

        if "product report" in lower_text:
            await self.send_product_report(chat_id)
            return
        elif "summary" in lower_text:
            await telegram_service.send_message(chat_id, "💰 <b>Summary Price</b>\nSelect period:", telegram_menu_service.get_date_menu("summary_price"))
            return
        elif "category" in lower_text:
            with next(get_db()) as db:
                categories = report_repo.get_all_categories(db)
                await telegram_service.send_message(
                    chat_id,
                    "📁 <b>Select Category</b>\nPlease choose a category to view its sales report:",
                    telegram_menu_service.get_category_list_menu(categories)
                )
            return
        elif "product" in lower_text:
            with next(get_db()) as db:
                products = report_repo.get_all_products(db)
                await telegram_service.send_message(
                    chat_id, 
                    "📦 <b>Select Product</b>\nPlease choose a product to view its sales report:",
                    telegram_menu_service.get_product_list_menu(products)
                )
            return
        elif "source" in lower_text:
            with next(get_db()) as db:
                sources = report_repo.get_all_sources(db)
                await telegram_service.send_message(
                    chat_id,
                    "📍 <b>Select Source</b>\nPlease choose a source:",
                    telegram_menu_service.get_source_list_menu(sources)
                )
            return
        elif "payment" in lower_text:
            with next(get_db()) as db:
                methods = report_repo.get_all_payment_methods(db)
                await telegram_service.send_message(
                    chat_id,
                    "💳 <b>Select Payment Method</b>\nPlease choose a payment method:",
                    telegram_menu_service.get_payment_list_menu(methods)
                )
            return
        elif "commission" in lower_text:
            with next(get_db()) as db:
                users = report_repo.get_all_users(db)
                await telegram_service.send_message(
                    chat_id,
                    "👤 <b>Select User</b>\nPlease choose a user to view their commission:",
                    telegram_menu_service.get_user_list_menu(users)
                )
            return
        elif "delivery" in lower_text:
            with next(get_db()) as db:
                types = report_repo.get_all_delivery_types(db)
                await telegram_service.send_message(
                    chat_id,
                    "🚚 <b>Select Delivery Type</b>\nPlease choose a delivery type:",
                    telegram_menu_service.get_delivery_list_menu(types)
                )
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
            await self._menu_reply(
                chat_id,
                "📊 <b>Shop Report Bot</b>\nMain menu restored. Please use the buttons below.",
                telegram_menu_service.get_reply_keyboard(),
            )
            user_states.pop(chat_id, None)
            return

        if data == "main_product_price":
            with next(get_db()) as db:
                products = report_repo.get_all_products(db)
                await self._menu_reply(chat_id, "📦 <b>Select Product</b>\nPlease choose a product to view its sales report:",
                    telegram_menu_service.get_product_list_menu(products)
                )
            return

        if data == "main_product_report":
            await self.send_product_report(chat_id)
            return

        if data == "main_category_price":
            with next(get_db()) as db:
                categories = report_repo.get_all_categories(db)
                await self._menu_reply(chat_id, "📁 <b>Select Category</b>\nPlease choose a category to view its sales report:",
                    telegram_menu_service.get_category_list_menu(categories)
                )
            return

        if data == "main_payment_price":
            with next(get_db()) as db:
                methods = report_repo.get_all_payment_methods(db)
                await self._menu_reply(chat_id, "💳 <b>Select Payment Method</b>\nPlease choose a payment method:",
                    telegram_menu_service.get_payment_list_menu(methods)
                )
            return

        if data == "main_source_price":
            with next(get_db()) as db:
                sources = report_repo.get_all_sources(db)
                await self._menu_reply(chat_id, "📍 <b>Select Source</b>\nPlease choose a source:",
                    telegram_menu_service.get_source_list_menu(sources)
                )
            return

        if data == "main_commission_user":
            with next(get_db()) as db:
                users = report_repo.get_all_users(db)
                await self._menu_reply(chat_id, "👤 <b>Select User</b>\nPlease choose a user to view their commission:",
                    telegram_menu_service.get_user_list_menu(users)
                )
            return

        if data == "main_delivery_type":
            with next(get_db()) as db:
                types = report_repo.get_all_delivery_types(db)
                await self._menu_reply(chat_id, "🚚 <b>Select Delivery Type</b>\nPlease choose a delivery type:",
                    telegram_menu_service.get_delivery_list_menu(types)
                )
            return

        if data.startswith("prod_select_"):
            product_id = data.replace("prod_select_", "")
            user_states[chat_id] = f"selected_prod_{product_id}"
            await self._menu_reply(chat_id, "📅 <b>Select Period</b>\nChoose a period for this product:",
                telegram_menu_service.get_date_menu("prod_detail")
            )
            return

        if data.startswith("cat_select_"):
            category_id = data.replace("cat_select_", "")
            user_states[chat_id] = f"selected_cat_{category_id}"
            await self._menu_reply(chat_id, "📅 <b>Select Period</b>\nChoose a period for this category:",
                telegram_menu_service.get_date_menu("cat_detail")
            )
            return

        if data.startswith("pay_select_"):
            method_name = data.replace("pay_select_", "")
            user_states[chat_id] = f"selected_pay_{method_name}"
            await self._menu_reply(chat_id, "📅 <b>Select Period</b>\nChoose a period for this payment method:",
                telegram_menu_service.get_date_menu("pay_detail")
            )
            return

        if data.startswith("src_select_"):
            source_name = data.replace("src_select_", "")
            user_states[chat_id] = f"selected_src_{source_name}"
            await self._menu_reply(chat_id, "📅 <b>Select Period</b>\nChoose a period for this source:",
                telegram_menu_service.get_date_menu("src_detail")
            )
            return

        if data.startswith("usr_select_"):
            user_id = data.replace("usr_select_", "")
            user_states[chat_id] = f"selected_usr_{user_id}"
            await self._menu_reply(chat_id, "📅 <b>Select Period</b>\nChoose a period for this user's commission:",
                telegram_menu_service.get_date_menu("usr_detail")
            )
            return

        if data.startswith("dlv_select_"):
            dlv_type = data.replace("dlv_select_", "")
            user_states[chat_id] = f"selected_dlv_{dlv_type}"
            await self._menu_reply(chat_id, "📅 <b>Select Period</b>\nChoose a period for this delivery type:",
                telegram_menu_service.get_date_menu("dlv_detail")
            )
            return

        if data.startswith("main_"):
            type_prefix = data.replace("main_", "")
            if type_prefix == "google_backup":
                await self.trigger_google_backup(chat_id)
                return
            if type_prefix == "product_report":
                await self.send_product_report(chat_id)
                return
            
            labels = {
                "summary_price": "💰 Summary Price",
                "category_price": "📁 Price by Category",
                "product_price": "📦 Price by Product",
                "source_price": "📍 Price by Source",
                "payment_price": "💳 Price by Payment",
                "commission_user": "👤 Commission by User",
                "delivery_type": "🚚 Price by Delivery Type"
            }
            title = labels.get(type_prefix, "Report")
            await self._menu_reply(chat_id, f"{title}\nSelect period:", 
                telegram_menu_service.get_date_menu(type_prefix)
            )
            return

        # Handle Product Detail Date Selection
        if data.startswith("prod_detail_"):
            period = data.replace("prod_detail_", "")
            state = user_states.get(chat_id, "")
            if not state.startswith("selected_prod_"):
                await telegram_service.send_message(chat_id, "⚠️ Session expired. Please start over.")
                return
            
            product_id = int(state.replace("selected_prod_", ""))
            start_date, end_date = self.get_date_range(period)
            
            with next(get_db()) as db:
                report_data = report_repo.get_single_product_summary(db, product_id, start_date, end_date)
                if not report_data:
                    await telegram_service.send_message(chat_id, "❌ Product not found.")
                    return
                
                msg = f"📦 <b>Product Summary</b>\n"
                msg += f"Product: <b>{report_data['name']}</b>\n"
                msg += f"Period: <b>{period.replace('_', ' ').title()}</b>\n\n"
                msg += f"💰 Total Sales: <b>${report_data['total_sales']:,.2f}</b>\n"
                msg += f"📦 Total Qty: <b>{report_data['total_qty']}</b>\n"
                
                await self._menu_reply(chat_id, msg,
                    telegram_menu_service.get_post_report_menu("product_price")
                )
            return

        # Handle Category Detail Date Selection
        if data.startswith("cat_detail_"):
            period = data.replace("cat_detail_", "")
            state = user_states.get(chat_id, "")
            if not state.startswith("selected_cat_"):
                await telegram_service.send_message(chat_id, "⚠️ Session expired. Please start over.")
                return

            category_id = int(state.replace("selected_cat_", ""))
            start_date, end_date = self.get_date_range(period)

            with next(get_db()) as db:
                report_data = report_repo.get_single_category_summary(db, category_id, start_date, end_date)
                if not report_data:
                    await telegram_service.send_message(chat_id, "❌ Category not found.")
                    return

                msg = f"📁 <b>Category Summary</b>\n"
                msg += f"Category: <b>{report_data['name']}</b>\n"
                msg += f"Period: <b>{period.replace('_', ' ').title()}</b>\n\n"
                msg += f"💰 Total Sales: <b>${report_data['total_sales']:,.2f}</b>\n"
                msg += f"📦 Total Qty: <b>{report_data['total_qty']}</b>\n"

                await self._menu_reply(chat_id, msg,
                    telegram_menu_service.get_post_report_menu("category_price")
                )
            return

        # Handle Payment Method Detail Date Selection
        if data.startswith("pay_detail_"):
            period = data.replace("pay_detail_", "")
            state = user_states.get(chat_id, "")
            if not state.startswith("selected_pay_"):
                await telegram_service.send_message(chat_id, "⚠️ Session expired. Please start over.")
                return

            method_name = state.replace("selected_pay_", "")
            start_date, end_date = self.get_date_range(period)

            with next(get_db()) as db:
                report_data = report_repo.get_single_payment_summary(db, method_name, start_date, end_date)
                if not report_data:
                    await telegram_service.send_message(chat_id, "❌ Payment method not found.")
                    return

                msg = f"💳 <b>Payment Summary</b>\n"
                msg += f"Method: <b>{method_name}</b>\n"
                msg += f"Period: <b>{period.replace('_', ' ').title()}</b>\n\n"
                msg += f"💰 Total Sales: <b>${report_data['total_sales']:,.2f}</b>\n"
                msg += f"📄 Total Invoices: <b>{report_data['total_invoices']}</b>\n"

                await self._menu_reply(chat_id, msg,
                    telegram_menu_service.get_post_report_menu("payment_price")
                )
            return

        # Handle Source Detail Date Selection
        if data.startswith("src_detail_"):
            period = data.replace("src_detail_", "")
            state = user_states.get(chat_id, "")
            if not state.startswith("selected_src_"):
                await telegram_service.send_message(chat_id, "⚠️ Session expired. Please start over.")
                return

            source_name = state.replace("selected_src_", "")
            start_date, end_date = self.get_date_range(period)

            with next(get_db()) as db:
                report_data = report_repo.get_single_source_summary(db, source_name, start_date, end_date)
                if not report_data:
                    await telegram_service.send_message(chat_id, "❌ Source not found.")
                    return

                msg = f"📍 <b>Source Summary</b>\n"
                msg += f"Source: <b>{source_name}</b>\n"
                msg += f"Period: <b>{period.replace('_', ' ').title()}</b>\n\n"
                msg += f"💰 Total Sales: <b>${report_data['total_sales']:,.2f}</b>\n"
                msg += f"📄 Total Invoices: <b>{report_data['total_invoices']}</b>\n"

                await self._menu_reply(chat_id, msg,
                    telegram_menu_service.get_post_report_menu("source_price")
                )
            return

        # Handle User Commission Detail Date Selection
        if data.startswith("usr_detail_"):
            period = data.replace("usr_detail_", "")
            state = user_states.get(chat_id, "")
            if not state.startswith("selected_usr_"):
                await telegram_service.send_message(chat_id, "⚠️ Session expired. Please start over.")
                return

            user_id = int(state.replace("selected_usr_", ""))
            start_date, end_date = self.get_date_range(period)

            with next(get_db()) as db:
                report_data = report_repo.get_single_user_commission(db, user_id, start_date, end_date)
                if not report_data:
                    await telegram_service.send_message(chat_id, "❌ User not found.")
                    return

                msg = f"👤 <b>Commission Summary</b>\n"
                msg += f"User: <b>{report_data['name']}</b>\n"
                msg += f"Period: <b>{period.replace('_', ' ').title()}</b>\n\n"
                msg += f"💰 Total Commission: <b>${report_data['total_commission']:,.2f}</b>\n"
                msg += f"💵 Total Sales: <b>${report_data['total_sales']:,.2f}</b>\n"
                msg += f"📦 Total Qty: <b>{report_data['total_qty']}</b>\n"

                await self._menu_reply(chat_id, msg,
                    telegram_menu_service.get_post_report_menu("commission_user")
                )
            return

        # Handle Delivery Type Detail Date Selection
        if data.startswith("dlv_detail_"):
            period = data.replace("dlv_detail_", "")
            state = user_states.get(chat_id, "")
            if not state.startswith("selected_dlv_"):
                await telegram_service.send_message(chat_id, "⚠️ Session expired. Please start over.")
                return

            dlv_type = state.replace("selected_dlv_", "")
            start_date, end_date = self.get_date_range(period)

            with next(get_db()) as db:
                report_data = report_repo.get_single_delivery_summary(db, dlv_type, start_date, end_date)
                if not report_data:
                    await telegram_service.send_message(chat_id, "❌ Delivery type not found.")
                    return

                msg = f"🚚 <b>Delivery Summary</b>\n"
                msg += f"Type: <b>{dlv_type}</b>\n"
                msg += f"Period: <b>{period.replace('_', ' ').title()}</b>\n\n"
                msg += f"💰 Total Sales: <b>${report_data['total_sales']:,.2f}</b>\n"
                msg += f"🚚 Delivery Fee: <b>${report_data['total_delivery_fee']:,.2f}</b>\n"
                msg += f"📄 Total Invoices: <b>{report_data['total_invoices']}</b>\n"

                await self._menu_reply(chat_id, msg,
                    telegram_menu_service.get_post_report_menu("delivery_type")
                )
            return

        # Date Pattern Actions
        if "_today" in data or "_3days" in data or "_7days" in data or "_1month" in data or "_all" in data or "_custom" in data:
            await self.process_date_callback(chat_id, data)

    async def process_date_callback(self, chat_id: str, data: str):
        parts = data.split("_")
        period = parts[-1]
        report_type = "_".join(parts[:-1])

        if period == "custom":
            user_states[chat_id] = f"waiting_{report_type}_range"
            await telegram_service.send_message(chat_id, "📅 <b>Custom Date Range</b>\nPlease input: <code>YYYY-MM-DD YYYY-MM-DD</code>\nExample: <code>2026-05-01 2026-05-08</code>")
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

    async def run_and_send_report(self, chat_id: str, report_type: str, start, end, label: str):
        db = SessionLocal()
        try:
            msg = ""
            if report_type == "summary_price": msg = report_service.format_summary_price(db, start, end, label)
            elif report_type == "category_price": msg = report_service.format_category_price(db, start, end, label)
            elif report_type == "product_price": msg = report_service.format_product_price(db, start, end, label)
            elif report_type == "source_price": msg = report_service.format_source_price(db, start, end, label)
            elif report_type == "payment_price": msg = report_service.format_payment_price(db, start, end, label)
            elif report_type == "commission_user": msg = report_service.format_commission_user(db, start, end, label)
            elif report_type == "delivery_type": msg = report_service.format_delivery_type_price(db, start, end, label)
            
            if msg:
                await telegram_service.send_message(chat_id, msg, telegram_menu_service.get_post_report_menu(report_type))
        except Exception as e:
            logger.error(f"Report error: {e}")
            await telegram_service.send_message(chat_id, "❌ Error generating report.")
        finally:
            db.close()

    async def send_product_report(self, chat_id: str):
        db = SessionLocal()
        try:
            messages = report_service.format_product_report_messages(db)
            for index, msg in enumerate(messages):
                # Keep keyboard only in last message to avoid clutter.
                reply_markup = telegram_menu_service.get_reply_keyboard() if index == len(messages) - 1 else None
                await telegram_service.send_message(chat_id, msg, reply_markup)
        except Exception as e:
            logger.error(f"Product report error: {e}")
            await telegram_service.send_message(chat_id, "❌ Error generating product report.")
        finally:
            db.close()

telegram_command_service = TelegramCommandService()
