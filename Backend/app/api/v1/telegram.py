from fastapi import APIRouter, Request, Header, HTTPException
from app.core.config import settings
from app.services.telegram_service import telegram_service
from app.services.telegram_command_service import telegram_command_service

router = APIRouter(prefix="/telegram", tags=["telegram"])

@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None)
):
    """
    Telegram webhook endpoint. 
    Handles main menu, reports, and custom range selection.
    """
    if settings.telegram_webhook_secret and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        return {"status": "unauthorized"}

    update = await request.json()
    await telegram_command_service.handle_update(update)
    return {"status": "ok"}

@router.post("/test-message")
async def send_test_message():
    """Manual test endpoint to verify Telegram integration."""
    if not settings.telegram_chat_id:
        raise HTTPException(status_code=400, detail="TELEGRAM_CHAT_ID not configured")
    
    result = await telegram_service.send_message(
        settings.telegram_chat_id, 
        "🔔 <b>Test Message</b>\nYour Telegram integration is working correctly!"
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to send message")
    return {"status": "success", "telegram_response": result}
