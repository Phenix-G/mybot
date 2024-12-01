import os

# Debug模式
DEBUG = os.environ.get("DEBUG", True)

# Redis配置
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PROTOCOL = int(os.getenv("REDIS_PROTOCOL", 3))
REDIS_PASSWORD = os.getenv(
    "REDIS_PASSWORD", ""
)


# Telegram配置
TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN", ""
)

# Web服务配置
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", 8000))
