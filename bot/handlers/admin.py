from telegram import Update
from telegram.ext import ContextTypes
import logging

from bot.utils.permission import admin_required
from bot.services.reader import (
    get_restart_uuid,
    get_deploy_url,
)
from bot.services.reader import get_web_status
from core.exceptions import handle_exception
from core.utils import send_message


@admin_required
async def get_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /getweb command"""
    text = await get_web_status()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


@admin_required
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command"""
    restart_uuid = get_restart_uuid()
    web_url = get_deploy_url()

    if not web_url:
        logging.warning("Cannot stop bot - web url has not been set")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Cannot stop bot - web url has not been set",
        )
        return

    if context.application.stop_event:
        logging.info("Stop command received, initiating shutdown...")
        try:
            text = [
                "Shutting down the bot...",
                f"Restart url: {web_url}/restart?uuid={restart_uuid}",
            ]
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text="\n".join(text)
            )
            context.application.stop_event.set()
        except Exception as e:
            handle_exception(
                e,
                message="Failed to send stop message",
                source="stop_command",
                notify_func=send_message,
            )
    else:
        logging.warning("Stop event not found")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Cannot stop bot - stop_event not configured",
        )
