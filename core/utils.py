from core.config import TELEGRAM_BOT_TOKEN, ADMIN_ID
from core.redis import redis_client

from telegram import Bot


# Get admin ID from Redis or config
admin_id = int(redis_client.get("admin") or ADMIN_ID)


def send_message(message: str, chat_id: int = admin_id):
    """Send message to bot"""

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_message(chat_id=chat_id, text=message)
