import asyncio
import logging
import threading

import uvicorn

from web import app
from bot import create_bot

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def run_web():
    uvicorn.run(app, host="0.0.0.0", port=8000)


def run_bot():
    asyncio.run(bot_main())


async def bot_main():
    # 创建一个事件用于停止bot
    stop_event = asyncio.Event()
    application = create_bot(stop_event)

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # 等待停止信号
    await stop_event.wait()

    # 收到停止信号后，正确关闭bot
    await application.updater.stop()
    await application.stop()
    await application.shutdown()
    logging.info("Bot has been stopped")


if __name__ == "__main__":
    # 启动web服务作为独立线程
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = False
    web_thread.start()
    logging.info("Web thread started")

    # 在主线程中运行bot
    try:
        run_bot()
    except Exception as e:
        logging.error(f"Bot exited with error: {e}")
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt")
