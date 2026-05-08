import httpx
import logging
import asyncio
from app.core.config import settings

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}"

    async def send_message(self, chat_id: str, text: str, reply_markup: dict | None = None):
        if not settings.telegram_bot_token:
            logger.warning("Telegram bot token is not set.")
            return

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to send Telegram message: {e}")
                return None

    async def edit_message(self, chat_id: str, message_id: int, text: str, reply_markup: dict | None = None):
        if not settings.telegram_bot_token:
            return

        url = f"{self.base_url}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to edit Telegram message: {e}")
                return None

    async def answer_callback(self, callback_query_id: str, text: str | None = None):
        if not settings.telegram_bot_token:
            return

        url = f"{self.base_url}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text

        async with httpx.AsyncClient() as client:
            try:
                await client.post(url, json=payload)
            except Exception as e:
                logger.error(f"Failed to answer callback: {e}")

    async def notify_checkout(self, invoice, items):
        if not settings.telegram_notify_enabled or not settings.telegram_chat_id:
            return

        try:
            msg = f"🧾 <b>New Checkout Completed</b>\n\n"
            msg += f"Invoice ID: {invoice.invoice_no}\n"
            msg += f"Customer: {invoice.customer_name or 'N/A'}\n"
            msg += f"Phone: {invoice.customer_phone or 'N/A'}\n"
            msg += f"Source: {invoice.source.capitalize()}\n"
            msg += f"Payment: {invoice.payment_method.capitalize()}\n"
            msg += f"Delivery: {invoice.delivery_type.capitalize()}\n"
            msg += f"Delivery Status: {invoice.delivery_status.capitalize()}\n\n"

            msg += "<b>Products:</b>\n"
            for i, item in enumerate(items, 1):
                msg += f"{i}. {item.product_name} x {item.quantity} = ${item.total:.2f}\n"

            msg += f"\nSubtotal: ${invoice.subtotal:.2f}\n"
            msg += f"Delivery Fee: ${invoice.delivery_price:.2f}\n"
            msg += f"Discount: {invoice.discount}%\n"
            msg += f"<b>Total: ${invoice.total:.2f}</b>\n\n"
            msg += f"Date: {invoice.created_at.strftime('%Y-%m-%d %H:%M')}"

            await self.send_message(settings.telegram_chat_id, msg)
        except Exception as e:
            logger.error(f"Error preparing Telegram notification: {e}")

telegram_service = TelegramService()
