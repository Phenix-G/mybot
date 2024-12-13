import asyncio
import logging
import threading
from typing import Optional

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from core.config import TELEGRAM_BOT_TOKEN
from core.exceptions import handle_exception
from bot.handlers.admin import stop, get_status
from bot.handlers.common import start, echo, unknown, get_id
from bot.handlers.operations import set_command, get_command, help_command


class TelegramBot:
    """Singleton Bot class"""

    _instance: Optional["TelegramBot"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event: Optional[asyncio.Event] = None
        self._lock = threading.Lock()

    def thread_start(self):
        """Start the bot thread"""
        with self._lock:
            if self._thread and self._thread.is_alive():
                logging.warning("Bot thread already running")
                return

            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            logging.info("Bot thread started")

    def thread_stop(self):
        """Stop the bot thread"""
        with self._lock:
            if self._stop_event:
                self._stop_event.set()
                if self._thread:
                    self._thread.join(timeout=5)  # Wait for thread to finish
                    self._thread = None
                    logging.info("Bot thread stopped")

    @property
    def is_running(self) -> bool:
        """Check if bot is running"""
        return bool(self._thread and self._thread.is_alive())

    def _create(self, stop_event=None):
        """Create and configure the bot application"""
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

        # Store stop_event in application object
        application.stop_event = stop_event

        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("status", get_status))
        application.add_handler(CommandHandler("stop", stop))
        application.add_handler(CommandHandler("getid", get_id))
        application.add_handler(CommandHandler("set", set_command))
        application.add_handler(CommandHandler("get", get_command))
        application.add_handler(CommandHandler("help", help_command))

        # Add message handlers
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
        application.add_handler(MessageHandler(filters.COMMAND, unknown))

        return application

    async def _polling(self, loop: asyncio.AbstractEventLoop):
        """Main bot polling logic"""
        try:
            self._stop_event = asyncio.Event()
            application = self._create(self._stop_event)

            await application.initialize()
            await application.start()
            await application.updater.start_polling()

            # Wait for stop signal
            await self._stop_event.wait()

            logging.info("Stopping bot...")
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
            logging.info("Bot has been completely stopped")
        except Exception as e:
            handle_exception(e, "Bot exited with error")

    def _loop(self):
        """Run bot in a new thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._polling(loop))
        loop.close()
