import functools
from typing import Callable, Any
import uuid

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
from core.config import TELEGRAM_BOT_TOKEN, WEB_PORT, ADMIN_ID
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
    redis_client.hset("page", mapping={data[0]: data[1]})

    if page:
        page.content = data[1]
    else:
        page = Page(name=data[0], content=data[1])
        session.add(page)

    session.commit()


@handle_redis_error
def set_access_granted_user(user_id: int):
    return redis_client.sadd("user", user_id)


@handle_redis_error
def set_cf_node(data: str):
    # sub1;sub2
    # remove begin and end space
    data = data.strip().split(";")
    # [sub1,sub2]
    return redis_client.sadd("cf_node", data)


def get_cf_node():
    data = redis_client.smembers("cf_node")
    result = "\n".join(data)
    return f"cf_node: [\n{result}\n]"


@handle_redis_error
def set_huggingface_path(data: str):
    # cf-aaa;container-bbb
    # remove begin and end space
    data = data.strip().split(";")
    # [cf-aaa,container-bbb]

    path = {}
    for item in data:
        key, value = item.split("-", 1)
        path[key] = value
    return redis_client.hset("path", mapping=path)


def get_huggingface_path(str_format=True):
    try:
        if str_format:
            data = redis_client.hgetall("path")
            result = "\n".join([f"{key}=>{value}" for key, value in data.items()])
            return f"path: [\n{result}\n]"

        else:
            return redis_client.hgetall("path")
    except Exception as e:
        logging.error(f"Failed to get huggingface path: {e}")
        return "path:path is not set"


@handle_redis_error
def set_web_url(url: str):
    return redis_client.set("web_url", url)


@handle_redis_error
def set_huggingface_url(url: str):
    return redis_client.set("huggingface_url", url)


@handle_redis_error
def set_node(node: str):
    # node-xxx
    # remove begin and end space
    node = node.strip().split("-", 1)
    return redis_client.hset("node", mapping={node[0]: node[1]})


def get_node():
    node = redis_client.hgetall("node")
    result = "\n".join([f"{key}=>{value}" for key, value in node.items()])
    return f"node: [\n{result}\n]"


def get_page():
    session = next(get_session())
    # get page
    page = session.exec(select(Page)).all()
    result = ";".join([f"{p.name}" for p in page])
    return f"page: {result}"


def get_huggingface_url():
    data = redis_client.get("huggingface_url")
    result = str(data) if data else ""
    return f"huggingface_url: {result}"


def get_access_granted_user():
    data = redis_client.smembers("user")
    result = ";".join(data)
    return f"user: {result}"


def get_huggingface_status():
    url = get_huggingface_url()

    if url:
        response = httpx.get(url)
    else:
        return "Huggingface url is not set"
    if response.status_code != 200:
        return f"Failed !!! {response.status_code}: {response.text}"
    return f"Huggingface is running. status: {response.status_code}"


def get_subscription():
    url = get_huggingface_url()
    if not url:
        return "Huggingface url is not set"

    path = get_huggingface_path(False)

    if isinstance(path, str):
        return path

    if path.get("cf"):
        cf_subscription = f'{url}/{path["cf"]}'
    else:
        cf_subscription = ""

    if path.get("container"):
        container_subscription = f'{url}/{path["container"]}'
    else:
        container_subscription = ""

    if cf_subscription and container_subscription:
        return f"subscription: [\ncf=>{cf_subscription}\ncontainer=>{container_subscription}\n]"
    elif cf_subscription:
        return f"subscription: \ncf=>{cf_subscription}"
    elif container_subscription:
        return f"subscription: \ncontainer=>{container_subscription}"
    else:
        return "subscription: \nNo subscription, please set huggingface url and path."


def get_restart_url():
    data = redis_client.get("web_url")
    restart_uuid = uuid.uuid4()
    redis_client.set("restart_uuid", f"{restart_uuid}")
    result = str(data) if data else ""
    return f"restart_url: {result}/restart?uuid={restart_uuid}"


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
        text="You are not allowed to use this command. Please contact the administrator.",
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
    if not has_permission(update.effective_chat.id):
        await not_allow(update, context)
        return

    try:
        response = httpx.get(f"http://localhost:{WEB_PORT}/")
        text = f"status: {response.status_code}"
    except Exception as e:
        logging.error(f"Failed to get web: {e}")
        text = f"Failed to get web: {e}"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_permission(update.effective_chat.id):
        await not_allow(update, context)
        return

    url = get_restart_url()
    if not url:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Restart url is not set"
        )
        return

    try:
        text = [
            "Shutting down the bot...",
            f"Restart link: {url}",
        ]
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="\n".join(text)
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

        elif key == "user":
            set_access_granted_user(value)

        elif key == "cf_node":
            set_cf_node(value)

        elif key == "huggingface":
            set_huggingface_url(value)

        elif key == "path":
            set_huggingface_path(value)

        elif key == "node":
            set_node(value)

        elif key == "web":
            set_web_url(value)

        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=f"Unknown key: {key}"
            )
            return

    except RuntimeError as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Error: {key} {str(e)}"
        )
        return

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

    try:
        if key == "all":
            text = "\n".join(
                [
                    get_page(),
                    get_access_granted_user(),
                    get_cf_node(),
                    get_huggingface_url(),
                    get_huggingface_path(),
                    get_node(),
                    get_subscription(),
                    get_restart_url(),
                ]
            )

            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        elif key == "page":
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_page(),
            )

        elif key == "user":
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_access_granted_user(),
            )

        elif key == "cf_node":
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_cf_node(),
            )

        elif key == "huggingface":
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_huggingface_url(),
            )
        elif key == "node":
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=get_node()
            )
        elif key == "path":
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=get_huggingface_path()
            )

        elif key == "subscription":
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=get_subscription()
            )

        elif key == "web":
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=get_restart_url()
            )

        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=f"Unknown key: {key}"
            )
    except Exception as e:
        logging.error(f"Failed to get {key}: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Failed to get {key}: {e}"
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
     <key> - page,  user, cf_node, huggingface, path, web
     page -> name-xxx
     user -> user_id
     cf_node -> sub1;sub2
     huggingface -> url
     path -> cf-aaa;container-bbb
     web -> url
/get <key> - 获取配置
     <key> - all, page, user, cf_node, huggingface, path, web, subscription
/status - 获取huggingface状态

"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_permission(update.effective_chat.id):
        await not_allow(update, context)
        return

    huggingface_info = get_huggingface_status()
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
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    return application
