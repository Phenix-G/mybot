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

cache_page = ""


# 初始化调度器
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动调度器并添加定时任务
    scheduler.add_job(keep_web_alive, "interval", seconds=INTERVAL_TIME)
    # 每7天检查一次数据库
    scheduler.add_job(keep_database_alive, "interval", days=7)

    scheduler.start()

    yield  # 应用在这里运行，直到关闭

    # 应用关闭时清理
    scheduler.shutdown()


def keep_web_alive():
    try:
        httpx.get(f"http://127.0.0.1:{WEB_PORT}/")
    except Exception as e:
        logging.error(f"Error: {e}")


def keep_database_alive():
    try:
        redis_client.ping()

    except Exception as e:
        logging.error(f"Error: {e}")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def index(session: Session = Depends(get_session)):
    global cache_page
    # get all page
    try:
        page = session.exec(select(Page)).all()
        if page:
            cache_page = random.choice(page).content
            return Response(content=cache_page, media_type="text/html")
        else:
            return Response(content="Hello, World!", media_type="text/html")
    except Exception as e:
        logging.error(f"Error: {e}")
        return Response(content=f"Error: {e}", media_type="text/html")


@app.get("/restart")
async def restart():
    try:
        # 设置停止事件
        stop_web_event.set()

        await asyncio.sleep(1)  # 等待1秒以确保响应能够发送
        python = sys.executable
        logging.info("Restarting program...")
        os.execl(python, python, *sys.argv)  # 使用exec重新启动程序

    except Exception as e:
        logging.error(f"Failed to restart program: {e}")
        # 重启失败时，清除停止事件，让服务继续运行
        stop_web_event.clear()
        return JSONResponse({"error": f"Failed to restart: {str(e)}"}, status_code=500)
