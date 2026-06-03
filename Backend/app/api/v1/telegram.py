from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.core.config import settings
from app.models import User
from app.services.auth_service import get_current_user, require_permission
from app.services.telegram_command_service import telegram_command_service
from app.services.telegram_service import telegram_service

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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized webhook")

    update = await request.json()
    await telegram_command_service.handle_update(update)
    return {"status": "ok"}

@router.post("/test-message")
async def send_test_message(
    _: User = Depends(get_current_user),
    __=Depends(require_permission("backup:manage")),
):
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
