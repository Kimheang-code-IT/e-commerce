import asyncio
import httpx
import sys
import os

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

async def set_commands():
    if not settings.telegram_bot_token:
        print("TELEGRAM_BOT_TOKEN not found in .env")
        return

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/setMyCommands"
    
    commands = [
        {"command": "start", "description": "Main Menu / Start Bot"},
        {"command": "summary", "description": "💰 Summary Price Report"},
        {"command": "category", "description": "📁 Price by Category Report"},
        {"command": "product", "description": "📦 Price by Product Report"},
        {"command": "source", "description": "📍 Price by Source Report"},
        {"command": "payment", "description": "💳 Price by Payment Method Report"},
        {"command": "commission", "description": "👤 Commission by User Report"},
        {"command": "delivery", "description": "🚚 Price by Delivery Type Report"},
        {"command": "help", "description": "❓ How to use this bot"}
    ]
    
    payload = {"commands": commands}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        if response.status_code == 200:
            print("Successfully set Telegram bot commands menu!")
        else:
            print(f"Failed to set commands: {response.status_code} {response.text}")

if __name__ == "__main__":
    asyncio.run(set_commands())
