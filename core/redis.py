from typing import Optional
import redis
from redis.connection import SSLConnection

from core.logger import logging
from core.config import (
    DEBUG,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PROTOCOL,
    REDIS_PASSWORD,
)


class RedisClient:
    _instance: Optional[redis.Redis] = None
    _pool: Optional[redis.ConnectionPool] = None

    @classmethod
    def get_instance(cls) -> Optional[redis.Redis]:
        if cls._instance is None:
            cls._instance = cls._create_client()
        return cls._instance

    @classmethod
    def _create_client(cls) -> Optional[redis.Redis]:
        if cls._pool is None:
            redis_config = {
                "host": REDIS_HOST,
                "port": REDIS_PORT,
                "decode_responses": True,
                "protocol": REDIS_PROTOCOL,
            }

            if not DEBUG:
                redis_config.update(
                    {"password": REDIS_PASSWORD, "connection_class": SSLConnection}
                )

            try:
                cls._pool = redis.ConnectionPool(**redis_config)
            except Exception as e:
                logging.error(f"Failed to create Redis pool: {e}")
                return None

        try:
            return redis.Redis(connection_pool=cls._pool)
        except Exception as e:
            logging.error(f"Failed to create Redis client: {e}")
            return None

    @classmethod
    def close(cls):
        """关闭Redis连接"""
        if cls._instance:
            cls._instance.close()
            cls._instance = None
        if cls._pool:
            cls._pool.disconnect()
            cls._pool = None


redis_client = RedisClient.get_instance()
