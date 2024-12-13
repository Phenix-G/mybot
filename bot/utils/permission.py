import functools
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from core.config import ADMIN_ID
from core.redis import redis_client

# Get admin ID from Redis or config
admin_id = int(redis_client.get("admin") or ADMIN_ID)


def has_permission(user_id: int, admin=True, access_granted_user=False) -> bool:
    """
    Check if user has required permissions
    Args:
        user_id: Telegram user ID
        admin: Whether admin permission is required
        access_granted_user: Whether access granted user permission is sufficient
    Returns:
        bool: True if user has permission, False otherwise
    """
    if access_granted_user:
        if str(user_id) in redis_client.smembers("user"):
            return True

    if admin:
        if user_id == admin_id:
            return True

    return False


async def not_allow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send not allowed message to user
    Args:
        update: Telegram update
        context: Telegram context
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="You are not allowed to use this command. Please contact the administrator.",
    )


def admin_required(func: Callable) -> Callable:
    """
    Decorator to check if user has admin permissions
    Args:
        func: Function to be decorated
    Returns:
        Wrapped function that checks permissions
    """

    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        if not has_permission(update.effective_chat.id):
            return await not_allow(update, context)
        return await func(update, context, *args, **kwargs)

    return wrapper
