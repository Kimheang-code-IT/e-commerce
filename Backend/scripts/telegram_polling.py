import asyncio
import httpx
import logging
import sys
import os

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.telegram_command_service import telegram_command_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def poll_telegram():
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in .env")
        return

    logger.info("Starting Telegram bot polling (V2 Simplified)...")
    base_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}"
    offset = 0

    async with httpx.AsyncClient(timeout=40) as client:
        while True:
            try:
                url = f"{base_url}/getUpdates?offset={offset}&timeout=30"
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    for update in data.get("result", []):
                        # Use the new centralized command service
                        await telegram_command_service.handle_update(update)
                        offset = update["update_id"] + 1
                else:
                    logger.error(f"Error polling: {response.status_code} {response.text}")
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(poll_telegram())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
