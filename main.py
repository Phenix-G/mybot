import logging

import uvicorn

from core.config import WEB_PORT
from web import app
from bot import TelegramBot


def main():
    # Configure web service
    config = uvicorn.Config(app=app, host="0.0.0.0", port=WEB_PORT, log_level="info")
    server = uvicorn.Server(config)
    bot = TelegramBot()
    try:
        # Start initial bot thread
        bot.thread_start()

        # Run web service (main thread)
        server.run()
    except KeyboardInterrupt:
        logging.info("Server shutdown by keyboard interrupt")
    finally:
        bot.thread_stop()


if __name__ == "__main__":
    main()
