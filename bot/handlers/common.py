from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="I'm a bot, please talk to me!"
    )

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /getid command"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Your Telegram ID is: {update.effective_chat.id}",
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo the user message"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=update.message.text
    )

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    ) 