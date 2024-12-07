import asyncio
from contextlib import asynccontextmanager
import os
import random
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Depends, Response
from fastapi.responses import JSONResponse
import httpx
from sqlmodel import Session, select

from core import logging, redis_client
from core.db import get_session
from core.config import INTERVAL_TIME, WEB_PORT
from model.page import Page

stop_web_event = asyncio.Event()

cache_page = "Hello, World!"


# 初始化调度器
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动调度器并添加定时任务
    scheduler.add_job(keep_web_alive, "interval", seconds=INTERVAL_TIME)

    scheduler.start()

    yield  # 应用在这里运行，直到关闭

    # 应用关闭时清理
    scheduler.shutdown()


def keep_web_alive():
    # 检查停止事件
    if stop_web_event.is_set():
        return
    try:
        httpx.get(f"http://127.0.0.1:{WEB_PORT}/")
    except Exception as e:
        logging.error(f"Error: {e}")


# 添加一个新的函数来处理关闭
def shutdown_scheduler():
    if scheduler.running:
        try:
            scheduler.shutdown(wait=False)
            logging.info("Scheduler shutdown completed")
        except Exception as e:
            logging.error(f"Error shutting down scheduler: {e}")


app = FastAPI(lifespan=lifespan, openapi_url=None)


@app.get("/")
async def index(name: str | None = None, session: Session = Depends(get_session)):
    global cache_page
    try:
        # 如果指定了name参数，查找对应的页面
        if name:
            sql_pages = session.exec(select(Page).where(Page.name == name)).first()
            redis_pages = redis_client.hget("page", name)

            if sql_pages and redis_pages:
                cache_page = random.choice([sql_pages.content, redis_pages])
            else:
                cache_page = sql_pages.content if sql_pages else redis_pages
            return Response(content=cache_page, media_type="text/html")

        # 如果没有指定name，随机返回一个页面
        sql_pages = session.exec(select(Page)).all()
        redis_pages = redis_client.hgetall("page")

        if sql_pages and redis_pages:
            source = random.choice([sql_pages, redis_pages.values()])
            page = random.choice(source)
            try:
                cache_page = page.content
            except:
                cache_page = page
        else:
            if sql_pages:
                cache_page = random.choice(sql_pages).content
            elif redis_pages:
                cache_page = random.choice(list(redis_pages.values()))
        return Response(content=cache_page, media_type="text/html")

    except Exception as e:
        logging.error(f"Error: {e}")
        return Response(content=f"Error: {e}", media_type="text/html", status_code=500)


@app.get("/telegram")
async def telegram(bot_token: str, chat_id: str, message: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    params = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": "true",
    }

    response = httpx.get(url, headers=headers, params=params)
    print(response.json())
    return JSONResponse(content=response.json())


@app.get("/restart")
async def restart(uuid: str):
    try:
        if uuid == redis_client.get("restart_uuid"):
            # 设置停止事件
            stop_web_event.set()
            # 关闭调度器
            shutdown_scheduler()

            await asyncio.sleep(1)  # 等待1秒以确保响应能够发送
            python = sys.executable
            logging.info("Restarting program...")
            os.execl(python, python, *sys.argv)  # 使用exec重新启动程序

        return JSONResponse({"message": "restart path invalid..."})

    except Exception as e:
        logging.error(f"Failed to restart program: {e}")
        # 重启失败时，清除停止事件，让服务继续运行
        stop_web_event.clear()
        return JSONResponse({"error": f"Failed to restart: {str(e)}"}, status_code=500)
