class TelegramMenuService:
    def get_main_menu(self):
        return {
            "inline_keyboard": [
                [{"text": "💰 Summary Price", "callback_data": "main_summary_price"}],
                [{"text": "📁 Price by Category", "callback_data": "main_category_price"}],
                [{"text": "📦 Price by Product", "callback_data": "main_product_price"}],
                [{"text": "📍 Price by Source", "callback_data": "main_source_price"}],
                [{"text": "💳 Price by Payment", "callback_data": "main_payment_price"}],
                [{"text": "👤 Commission by User", "callback_data": "main_commission_user"}],
                [{"text": "🚚 Price by Delivery Type", "callback_data": "main_delivery_type"}],
                [{"text": "❓ Help", "callback_data": "main_help"}]
            ]
        }

    def get_date_menu(self, prefix: str):
        return {
            "inline_keyboard": [
                [{"text": "📅 Today", "callback_data": f"{prefix}_today"}],
                [{"text": "📅 Last 3 Days", "callback_data": f"{prefix}_3days"}],
                [{"text": "📅 Last 7 Days", "callback_data": f"{prefix}_7days"}],
                [{"text": "📅 Last 1 Month", "callback_data": f"{prefix}_1month"}],
                [{"text": "📅 All", "callback_data": f"{prefix}_all"}],
                [{"text": "🗓 Custom Date Range", "callback_data": f"{prefix}_custom"}],
                [{"text": "⬅️ Back to Main Menu", "callback_data": "back_main"}]
            ]
        }

    def get_post_report_menu(self, prefix: str):
        # Prefix here is the clean report type e.g. summary_price
        return {
            "inline_keyboard": [
                [{"text": "🔄 Choose Again", "callback_data": f"main_{prefix}"}],
                [{"text": "⬅️ Main Menu", "callback_data": "back_main"}]
            ]
        }

    def get_reply_keyboard(self):
        return {
            "keyboard": [
                [{"text": "💰 Summary"}, {"text": "📁 Category"}],
                [{"text": "📦 Product"}, {"text": "📍 Source"}],
                [{"text": "💳 Payment"}, {"text": "👤 Commission"}],
                [{"text": "🚚 Delivery"}, {"text": "❓ Help"}]
            ],
            "resize_keyboard": True,
            "persistent": True
        }

    def get_product_list_menu(self, products):
        keyboard = []
        for p in products:
            keyboard.append([{"text": f"📦 {p['name']}", "callback_data": f"prod_select_{p['id']}"}])
        
        keyboard.append([{"text": "⬅️ Back to Main Menu", "callback_data": "back_main"}])
        return {"inline_keyboard": keyboard}

telegram_menu_service = TelegramMenuService()
