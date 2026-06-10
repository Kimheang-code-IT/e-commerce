class TelegramMenuService:
    def get_main_menu(self):
        return {
            "inline_keyboard": [
                [{"text": "📦 Product Report", "callback_data": "main_product_report"}],
                [{"text": "📁 Category Report", "callback_data": "main_category_price"}],
                [{"text": "💳 Payment Report", "callback_data": "main_payment_price"}],
                [{"text": "🎁 Reward Report", "callback_data": "main_reward_product"}],
                [{"text": "👤 Commission Report", "callback_data": "main_commission_user"}],
                [{"text": "📊 Backup Google Sheets", "callback_data": "main_google_backup"}]
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
                [{"text": "📦 Product Report"}, {"text": "📁 Category"}],
                [{"text": "💳 Payment"}, {"text": "🎁 Reward"}],
                [{"text": "👤 Commission"}, {"text": "📊 Backup Google Sheets"}],
            ],
            "resize_keyboard": True,
        }

    def get_product_list_menu(self, products):
        keyboard = [[{"text": "📦 All Products", "callback_data": "prod_select_all"}]]
        for p in products:
            keyboard.append([{"text": f"📦 {p['name']}", "callback_data": f"prod_select_{p['id']}"}])
        keyboard.append([{"text": "⬅️ Back to Main Menu", "callback_data": "back_main"}])
        return {"inline_keyboard": keyboard}

    def get_category_list_menu(self, categories):
        keyboard = [[{"text": "📁 All Categories", "callback_data": "cat_select_all"}]]
        for c in categories:
            keyboard.append([{"text": f"📁 {c['name']}", "callback_data": f"cat_select_{c['id']}"}])
        keyboard.append([{"text": "⬅️ Back to Main Menu", "callback_data": "back_main"}])
        return {"inline_keyboard": keyboard}

    def get_payment_list_menu(self, methods):
        keyboard = [[{"text": "💳 All Payment Methods", "callback_data": "pay_select_all"}]]
        for m in methods:
            name = m['payment_method']
            keyboard.append([{"text": f"💳 {name}", "callback_data": f"pay_select_{name}"}])
        keyboard.append([{"text": "⬅️ Back to Main Menu", "callback_data": "back_main"}])
        return {"inline_keyboard": keyboard}

    def get_reward_list_menu(self, rewards):
        keyboard = [[{"text": "🎁 All Rewards", "callback_data": "rwd_select_all"}]]
        for reward in rewards:
            keyboard.append(
                [{"text": f"🎁 {reward['name']}", "callback_data": f"rwd_select_{reward['id']}"}]
            )
        keyboard.append([{"text": "⬅️ Back to Main Menu", "callback_data": "back_main"}])
        return {"inline_keyboard": keyboard}

    def get_source_list_menu(self, sources):
        keyboard = []
        for s in sources:
            name = s['source']
            keyboard.append([{"text": f"📍 {name}", "callback_data": f"src_select_{name}"}])
        keyboard.append([{"text": "⬅️ Back to Main Menu", "callback_data": "back_main"}])
        return {"inline_keyboard": keyboard}

    def get_user_list_menu(self, users):
        keyboard = [[{"text": "👤 All Sellers", "callback_data": "usr_select_all"}]]
        for u in users:
            keyboard.append([{"text": f"👤 {u['name']}", "callback_data": f"usr_select_{u['id']}"}])
        keyboard.append([{"text": "⬅️ Back to Main Menu", "callback_data": "back_main"}])
        return {"inline_keyboard": keyboard}

    def get_delivery_list_menu(self, types):
        keyboard = []
        for t in types:
            name = t['delivery_type']
            keyboard.append([{"text": f"🚚 {name}", "callback_data": f"dlv_select_{name}"}])
        keyboard.append([{"text": "⬅️ Back to Main Menu", "callback_data": "back_main"}])
        return {"inline_keyboard": keyboard}

telegram_menu_service = TelegramMenuService()
