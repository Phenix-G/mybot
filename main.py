import asyncio
import threading

import uvicorn

from bot import create_bot
from core import logging
from web import app


def run_web():
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,  # 生产环境设为False
    )
    server = uvicorn.Server(config)
    server.run()


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
    logging.info("Bot has been stopped")
    await application.updater.stop()
    await application.stop()
    await application.shutdown()


def main():
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


if __name__ == "__main__":
    main()

