import logging
from datetime import timedelta
from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.repositories.report_repository import report_repo
from app.services.telegram_service import telegram_service
from app.services.telegram_menu_service import telegram_menu_service
from app.services.report_service import report_service
from app.utils.timezone import cambodia_now

logger = logging.getLogger(__name__)

# Simple in-memory state store: chat_id -> state_name
user_states = {}

class TelegramCommandService:
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
        if not settings.telegram_report_enabled:
            return

        if "callback_query" in update:
            await self.handle_callback(update["callback_query"])
        elif "message" in update:
            await self.handle_message(update["message"])

    async def handle_message(self, message: dict):
        chat_id = str(message["chat"]["id"])
        text = message.get("text", "").strip()

        if chat_id != settings.telegram_chat_id:
            await telegram_service.send_message(chat_id, "🚫 Unauthorized.")
            return

        # Check for /start or /help
        if text.startswith("/"):
            command = text.split("@")[0] # handle /start@bot_name

            if command in ["/start", "/help"]:
                msg = "📊 <b>Shop Report Bot</b>\n\n"
                msg += "Please choose report type from the menu below:"
                await telegram_service.send_message(
                    chat_id, 
                    msg, 
                    telegram_menu_service.get_reply_keyboard()
                )
                user_states.pop(chat_id, None)
                return
            
            # Direct slash commands for reports
            elif command == "/summary":
                await telegram_service.send_message(chat_id, "💰 <b>Summary Price</b>\nSelect period:", telegram_menu_service.get_date_menu("summary_price"))
                return
            elif command == "/category":
                await telegram_service.send_message(chat_id, "📁 <b>Price by Category</b>\nSelect period:", telegram_menu_service.get_date_menu("category_price"))
                return
            elif command == "/product":
                with next(get_db()) as db:
                    products = report_repo.get_all_products(db)
                    await telegram_service.send_message(
                        chat_id, 
                        "📦 <b>Select Product</b>\nPlease choose a product to view its sales report:",
                        telegram_menu_service.get_product_list_menu(products)
                    )
                return
            elif command == "/source":
                await telegram_service.send_message(chat_id, "📍 <b>Price by Source</b>\nSelect period:", telegram_menu_service.get_date_menu("source_price"))
                return
            elif command == "/payment":
                await telegram_service.send_message(chat_id, "💳 <b>Price by Payment</b>\nSelect period:", telegram_menu_service.get_date_menu("payment_price"))
                return
            elif command == "/commission":
                await telegram_service.send_message(chat_id, "👤 <b>Commission by User</b>\nSelect period:", telegram_menu_service.get_date_menu("commission_user"))
                return
            elif command == "/delivery":
                await telegram_service.send_message(chat_id, "🚚 <b>Price by Delivery Type</b>\nSelect period:", telegram_menu_service.get_date_menu("delivery_type"))
                return

        # Handle Reply Keyboard Text
        lower_text = text.lower()
        if "summary" in lower_text:
            await telegram_service.send_message(chat_id, "💰 <b>Summary Price</b>\nSelect period:", telegram_menu_service.get_date_menu("summary_price"))
            return
        elif "category" in lower_text:
            await telegram_service.send_message(chat_id, "📁 <b>Price by Category</b>\nSelect period:", telegram_menu_service.get_date_menu("category_price"))
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
            await telegram_service.send_message(chat_id, "📍 <b>Price by Source</b>\nSelect period:", telegram_menu_service.get_date_menu("source_price"))
            return
        elif "payment" in lower_text:
            await telegram_service.send_message(chat_id, "💳 <b>Price by Payment</b>\nSelect period:", telegram_menu_service.get_date_menu("payment_price"))
            return
        elif "commission" in lower_text:
            await telegram_service.send_message(chat_id, "👤 <b>Commission by User</b>\nSelect period:", telegram_menu_service.get_date_menu("commission_user"))
            return
        elif "delivery" in lower_text:
            await telegram_service.send_message(chat_id, "🚚 <b>Price by Delivery Type</b>\nSelect period:", telegram_menu_service.get_date_menu("delivery_type"))
            return
        elif "help" in lower_text or "❓" in lower_text:
            await telegram_service.send_message(chat_id, "📊 <b>Shop Report Bot</b>\nPlease choose report type from the menu below:")
            return

        # Fallback: Restore keyboard for any unknown input
        await telegram_service.send_message(
            chat_id, 
            "❓ I didn't recognize that. Please use the menu below:", 
            telegram_menu_service.get_reply_keyboard()
        )

        # Handle Custom Date Range Input
        state = user_states.get(chat_id)
        if state and state.startswith("waiting_"):
            await self.process_custom_range(chat_id, text, state)
            return

    async def handle_callback(self, query: dict):
        chat_id = str(query["message"]["chat"]["id"])
        message_id = query["message"]["message_id"]
        data = query.get("data", "")

        if chat_id != settings.telegram_chat_id:
            await telegram_service.answer_callback(query["id"], "Unauthorized")
            return

        await telegram_service.answer_callback(query["id"])

        # Main Menu Actions
        if data == "back_main":
            await telegram_service.edit_message(
                chat_id, message_id, 
                "📊 <b>Shop Report Bot</b>\nMain menu restored. Please use the buttons below.", 
                None # Remove the inline keyboard
            )
            user_states.pop(chat_id, None)
            return

        if data == "main_product_price":
            with next(get_db()) as db:
                products = report_repo.get_all_products(db)
                await telegram_service.edit_message(
                    chat_id, message_id,
                    "📦 <b>Select Product</b>\nPlease choose a product to view its sales report:",
                    telegram_menu_service.get_product_list_menu(products)
                )
            return

        if data.startswith("prod_select_"):
            product_id = data.replace("prod_select_", "")
            user_states[chat_id] = f"selected_prod_{product_id}"
            await telegram_service.edit_message(
                chat_id, message_id,
                "📅 <b>Select Period</b>\nChoose a period for this product:",
                telegram_menu_service.get_date_menu("prod_detail")
            )
            return

        if data.startswith("main_"):
            type_prefix = data.replace("main_", "")
            if type_prefix == "help":
                await telegram_service.edit_message(
                    chat_id, message_id, 
                    "❓ <b>Help</b>\nSelect a report type and period to begin.", 
                    telegram_menu_service.get_main_menu()
                )
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
            await telegram_service.edit_message(
                chat_id, message_id, 
                f"{title}\nSelect period:", 
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
                
                await telegram_service.edit_message(
                    chat_id, message_id, msg,
                    telegram_menu_service.get_post_report_menu("product_price")
                )
            return

        # Date Pattern Actions
        elif "_today" in data or "_3days" in data or "_7days" in data or "_1month" in data or "_all" in data or "_custom" in data:
            await self.process_date_callback(chat_id, message_id, data)

    async def process_date_callback(self, chat_id: str, message_id: int, data: str):
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

telegram_command_service = TelegramCommandService()
