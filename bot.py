import httpx
from telegram import Update
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from core import logging
from core.config import TELEGRAM_BOT_TOKEN, WEB_PORT


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


async def get_web(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = httpx.get(f"http://localhost:{WEB_PORT}/")
        text = response.text
    except Exception as e:
        logging.error(f"Failed to get web: {e}")
        text = f"Failed to get web: {e}"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Shutting down the bot..."
        )
    except Exception as e:
        logging.error(f"Failed to send message: {e}")
    finally:
        # 触发停止事件
        context.application.stop_event.set()


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=update.message.text
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


def create_bot(stop_event=None):
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # 保存stop_event到application对象中
    application.stop_event = stop_event

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("getweb", get_web))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    return application
