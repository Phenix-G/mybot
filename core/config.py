import os
import pathlib
import logging

import pytz
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = pathlib.Path(__file__).parent.parent
# Timezone configuration
TIMEZONE = pytz.timezone("Asia/Shanghai")

# Debug mode
DEBUG = os.environ.get("DEBUG", False)

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PROTOCOL = int(os.getenv("REDIS_PROTOCOL", 3))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# MySQL configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "mybot")
MYSQL_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Admin ID
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

# Web service configuration
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", 8000))
INTERVAL_TIME = int(os.getenv("INTERVAL_TIME", 60))

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 直接配置日志
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)

# 禁用 httpx 日志
logging.getLogger("httpx").setLevel(logging.WARNING)
