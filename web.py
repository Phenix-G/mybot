import asyncio
import os
import sys

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from core import logging

app = FastAPI()
stop_web_event = asyncio.Event()


@app.get("/")
async def root():
    return {"message": "Hello World"}


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
