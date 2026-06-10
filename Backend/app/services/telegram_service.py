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
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
            try:
                response = await client.post(url, json=payload)
                data = response.json()
                if not data.get("ok"):
                    logger.error(
                        "Telegram sendMessage failed (chat=%s status=%s): %s",
                        chat_id,
                        response.status_code,
                        data,
                    )
                    return None
                return data
            except Exception as e:
                logger.error("Failed to send Telegram message to %s: %s", chat_id, e)
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

    async def notify_checkout(self, invoice, items, *, seller_name: str = ""):
        if not settings.telegram_notify_enabled or not settings.telegram_chat_id:
            return

        try:
            seller = (seller_name or "").strip() or "N/A"
            msg = f"🧾 <b>New Checkout Completed</b>\n\n"
            msg += f"Invoice ID: {invoice.invoice_no}\n"
            msg += f"Customer: {invoice.customer_name or 'N/A'}\n"
            msg += f"Phone: {invoice.customer_phone or 'N/A'}\n"
            msg += f"Payment: {invoice.payment_method.capitalize()}\n"
            msg += f"Delivery: {invoice.delivery_type.capitalize()}\n"
            msg += f"Delivery Status: {invoice.delivery_status.capitalize()}\n\n"

            msg += "<b>Products:</b>\n"
            for i, item in enumerate(items, 1):
                qty = int(item.quantity or 0)
                unit = float(item.price or 0)
                line_total = float(item.total or 0)
                if qty > 0 and unit <= 0 and line_total > 0:
                    unit = line_total / qty
                msg += f"{i}. {item.product_name} x {qty} @ ${unit:.2f} = ${line_total:.2f}\n"

            subtotal = float(invoice.subtotal or 0)
            discount = float(invoice.discount or 0)
            delivery_fee = float(invoice.delivery_price or 0)
            grand_total = max(0.0, subtotal - discount + delivery_fee)
            msg += f"\nSubtotal: ${subtotal:.2f}\n"
            msg += f"Delivery Fee: ${delivery_fee:.2f}\n"
            msg += f"Discount: ${discount:.2f}\n"
            msg += f"<b>Total: ${grand_total:.2f}</b>\n\n"
            msg += f"Date: {invoice.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            msg += f"By: {seller}"

            await self.send_message(settings.telegram_chat_id, msg)
        except Exception as e:
            logger.error(f"Error preparing Telegram notification: {e}")

    async def notify_refund(
        self,
        *,
        invoice_no: str,
        customer: str = "",
        phone: str = "",
        source: str = "",
        seller: str = "",
        reason: str = "",
        refunded_by: str = "",
        lines: list[dict],
    ):
        if not settings.telegram_notify_enabled or not settings.telegram_chat_id:
            return

        try:
            msg = "↩️ <b>Refund Completed</b>\n\n"
            msg += f"Invoice: {invoice_no}\n"
            msg += f"Customer: {customer or 'N/A'}\n"
            if phone:
                msg += f"Phone: {phone}\n"
            if seller:
                msg += f"Seller: {seller}\n"
            if refunded_by:
                msg += f"Refunded by: {refunded_by}\n"
            if reason:
                msg += f"Reason: {reason}\n"
            msg += "\n<b>Products returned to stock:</b>\n"
            total = 0.0
            for i, line in enumerate(lines, 1):
                name = line.get("product") or "—"
                qty = int(line.get("qty") or 0)
                amount = float(line.get("amount") or 0)
                unit = float(line.get("price") or 0)
                if qty > 0 and unit <= 0 and amount > 0:
                    unit = amount / qty
                total += amount
                if qty > 0:
                    msg += f"{i}. {name} x {qty} @ ${unit:.2f} = ${amount:.2f}\n"
                else:
                    msg += f"{i}. {name} = ${amount:.2f}\n"
            msg += f"\n<b>Refund total: ${total:.2f}</b>"
            await self.send_message(settings.telegram_chat_id, msg)
        except Exception as e:
            logger.error("Error preparing Telegram refund notification: %s", e)

telegram_service = TelegramService()
