import os

# Debug模式
DEBUG = os.environ.get("DEBUG", False)

# Redis配置
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PROTOCOL = int(os.getenv("REDIS_PROTOCOL", 3))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")


# MySQL配置
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "mybot")
MYSQL_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
# Telegram配置
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# 管理员ID
ADMIN_ID = os.getenv("ADMIN_ID", "")

# Web服务配置
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", 8000))
INTERVAL_TIME = int(os.getenv("INTERVAL_TIME", 60))

# Huggingface配置
HUGGINGFACE_URL = os.getenv("HUGGINGFACE_URL", "")
