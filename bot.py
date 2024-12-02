import functools
from typing import Callable, Any

import httpx
from sqlmodel import select
from telegram import Update
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from core import logging, redis_client
from core.config import HUGGINGFACE_URL, TELEGRAM_BOT_TOKEN, WEB_PORT, ADMIN_ID
from core.db import get_session
from model.page import Page


admin_id = int(redis_client.get("admin") or ADMIN_ID)


def handle_redis_error(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Redis operation failed in {func.__name__}: {str(e)}")
            raise RuntimeError(f"Failed to perform Redis operation: {str(e)}")

    return wrapper


def set_page(data: str):
    # name-xxx
    # remove begin and end space
    data = data.strip().split("-", 1)
    session = next(get_session())
    # get page
    page = session.exec(select(Page).where(Page.name == data[0])).first()

    if page:
        page.content = data[1]
    else:
        page = Page(name=data[0], content=data[1])
        session.add(page)

    session.commit()


@handle_redis_error
def set_cf_key(key: str):
    return redis_client.set("cf_key", key)


@handle_redis_error
def set_access_granted_user(user_id: int):
    return redis_client.sadd("user", user_id)


@handle_redis_error
def set_huggingface_url(url: str):
    return redis_client.set("huggingface_url", url)


@handle_redis_error
def set_subscription_base(data: str):
    # cf-aaa;huggingface-bbb
    # remove begin and end space
    data = data.strip().split(";")
    # [cf-aaa,huggingface-bbb]
    subscription = {}
    for item in data:
        key, value = item.split("-", 1)
        subscription[key] = value
    return redis_client.hset("subscription_base", mapping=subscription)


@handle_redis_error
def set_subscription_path(path: str):
    return redis_client.set("path", path)


def get_page():
    result = redis_client.hgetall("page")
    return ";".join(result.keys())


def get_cf_key():
    return redis_client.get("cf_key")


def get_huggingface_url():
    return redis_client.get("huggingface_url")


def get_access_granted_user():
    return redis_client.smembers("user")


def get_huggingface_info():
    url = redis_client.get("huggingface_url")

    if url:
        response = httpx.get(url)
    else:
        response = httpx.get(HUGGINGFACE_URL)
    if response.status_code != 200:
        return f"Failed !!! {response.status_code}: {response.text}"
    return "Huggingface is running"


def get_subscription_base():
    return redis_client.hgetall("subscription_base")


def get_subscription_path():
    return redis_client.get("path")


def get_subscription():
    subscription = ""
    base = get_subscription_base()
    path = get_subscription_path()
    if not base or not path:
        return "No subscription, please set subscription and path."
    for key, value in base.items():
        subscription += f"{key}:{value}/{path}\n"
    return subscription


def has_permission(user_id: int, admin=True, access_granted_user=False):
    if access_granted_user:
        if user_id in get_access_granted_user():
            return True

    if admin:
        if user_id == admin_id:
            return True

    return False


async def not_allow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="You are not allowed to use this command. Please contact the administrator",
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Your Telegram ID is: {update.effective_chat.id}",
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


async def set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_permission(update.effective_chat.id):
        await not_allow(update, context)
        return

    data = update.message.text
    data = data.split(" ", 2)
    if len(data) < 3:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"input format: /set <key> <value>"
        )
        return

    command, key, value = data
    try:
        if key == "page":
            set_page(value)

        elif key == "cf_key":
            set_cf_key(value)

        elif key == "user":
            set_access_granted_user(value)

        elif key == "huggingface":
            set_huggingface_url(value)

        elif key == "subscription":
            set_subscription_base(value)

        elif key == "path":
            set_subscription_path(value)

    except RuntimeError as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Error: {key} {str(e)}"
        )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"Successfully set {key}"
    )


async def get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_permission(update.effective_chat.id):
        await not_allow(update, context)
        return

    data = update.message.text
    data = data.split(" ", 1)
    if len(data) < 2:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"input format: /get <key>"
        )
        return

    command, key = data
    if key == "all":
        text = f"""
page: {get_page()}
cf_key: {get_cf_key()}
access_granted: {get_access_granted_user()}
huggingface_url: {get_huggingface_url()}
subscription: {get_subscription_base()}
path: {get_subscription_path()}
"""
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    elif key == "page":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"page: {get_page()}",
        )
    elif key == "cf_key":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"cf_key: {get_cf_key()}",
        )
    elif key == "user":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"access_granted_user: {get_access_granted_user()}",
        )
    elif key == "huggingface":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"huggingface_url: {get_huggingface_url()}",
        )
    elif key == "subscription":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"subscription: {get_subscription()}",
        )
    elif key == "path":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"path: {get_subscription_path()}",
        )
    elif key == "subscription_base":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"subscription_base: {get_subscription_base()}",
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Unknown key: {key}"
        )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_permission(update.effective_chat.id):
        await not_allow(update, context)
        return

    text = """
/start - 启动bot
/getweb - 获取web页面
/stop - 停止bot
/getid - 获取telegram id
/set <key> <value> - 设置配置
     <key> - page, cf_key, user, huggingface, subscription, path
     page -> name-xxx
     cf_key -> xxx
     user -> user_id
     huggingface -> url
     subscription -> cf aaa;huggingface bbb
     path -> path
/get <key> - 获取配置
     <key> - page, cf_key, user, huggingface, path, subscription_base, subscription
"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def huggingface(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_permission(update.effective_chat.id):
        await not_allow(update, context)
        return

    huggingface_info = get_huggingface_info()
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=huggingface_info
    )


def create_bot(stop_event=None):
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # 保存stop_event到application对象中
    application.stop_event = stop_event

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("getweb", get_web))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("getid", get_id))
    application.add_handler(CommandHandler("set", set))
    application.add_handler(CommandHandler("get", get))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("huggingface", huggingface))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    return application
