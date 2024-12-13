from telegram import Update
from telegram.ext import ContextTypes


from bot.utils.permission import admin_required
from bot.services import page
from bot.services.reader import (
    get_alive_url,
    get_all_config,
    get_access_granted_users,
    get_cf_node,
    get_deploy_url,
    get_path,
)
from bot.services.writer import (
    set_access_granted_user,
    set_cf_node,
    set_path,
    set_deploy_url,
    set_alive_url,
)
from core.exceptions import handle_exception


@admin_required
async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /set command"""
    data = update.message.text.split(" ", 2)
    if len(data) < 3:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Input format: /set <key> <value>"
        )
        return

    _, key, value = data
    try:
        if key == "page":
            await page.set_page(value)
        elif key == "user":
            print(value)
            await set_access_granted_user(value)
        elif key == "cf_node":
            await set_cf_node(value)
        elif key == "alive":
            await set_alive_url(value)
        elif key == "path":
            await set_path(value)
        elif key == "web":
            await set_deploy_url(value)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=f"Unknown key: {key}"
            )
            return

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Successfully set {key}"
        )
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Error setting {key}: {str(e)}"
        )


@admin_required
async def get_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /get command"""
    data = update.message.text.split(" ", 1)
    if len(data) < 2:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Input format: /get <key>"
        )
        return

    _, key = data
    try:
        if key == "all":
            text = get_all_config()
        elif key == "page":
            text = page.get_pages()
        elif key == "user":
            text = get_access_granted_users()
        elif key == "cf_node":
            text = get_cf_node()
        elif key == "alive":
            text = get_alive_url()
        elif key == "path":
            text = get_path()
        elif key == "web":
            text = get_deploy_url()
        else:
            text = f"Unknown key: {key}"

        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    except Exception as e:
        handle_exception(e, f"Failed to get {key}", source="get_command")
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Error getting {key}: {str(e)}"
        )


@admin_required
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    text = """
Available commands:
/start - Start the bot
/status - Get web status
/stop - Stop the bot
/getid - Get your Telegram ID
/set <key> <value> - Set configuration
    Keys => page, user, cf_node, alive, path, web
    page: web page => name-content  /  name-url
    user: grant access => user_id
    cf_node: cf node url => url;url
    alive: keep web alive => url;url
    path: subscription path => cf-aaa;container-bbb
    web: deploy url => url
/get <key> - Get configuration
    Keys: all, page, user, cf_node, alive, path, web
"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
