import asyncio
import uuid

import httpx

from core.exceptions import handle_exception
from core.redis import redis_client


def get_cf_node():
    """Get CF nodes"""
    data = redis_client.smembers("cf_node")
    result = "\n".join(data)
    return f"cf_node: [\n{result}\n]"


def get_path():
    """Get huggingface paths"""
    data = redis_client.hgetall("path")
    result = "\n".join([f"{key}=>{value}" for key, value in data.items()])
    return f"path: [\n{result}\n]"


def get_access_granted_users():
    """Get access granted users"""
    data = redis_client.smembers("user")
    result = ";".join(data)
    return f"user: {result}"


def get_all_config():
    """Get all configurations"""
    return "\n".join(
        [
            get_access_granted_users(),
            get_cf_node(),
            get_path(),
            get_alive_url(),
            f"web: {get_deploy_url()}",
        ]
    )


def get_alive_url():
    """Get alive url"""
    url = redis_client.smembers("alive")
    if not url:
        return "alive url is not set"
    text = "\n".join(url)
    return f"alive: [\n{text}\n]"


def get_restart_uuid():
    """Get restart uuid"""
    restart_uuid = uuid.uuid4()
    redis_client.set("restart_uuid", f"{restart_uuid}")
    return restart_uuid


def get_deploy_url():
    """Get deploy url"""
    deploy_url = redis_client.get("deploy_url")
    return deploy_url


async def check_web_status(url: str, client: httpx.AsyncClient) -> str:
    """Check single URL status"""
    try:
        response = await client.get(url)
        if response.status_code != 200:
            return f"{url} is error, status: {response.status_code}\n"
        return f"{url} is ok\n"
    except Exception as e:
        return f"{url} is error: {str(e)}\n"


async def get_web_status() -> str:
    """Get status of all web URLs"""
    try:
        urls = redis_client.smembers("alive")
        if not urls:
            return "Keep alive urls is not been set"

        """Concurrently check all URLs"""
        async with httpx.AsyncClient() as client:
            tasks = [check_web_status(url, client) for url in urls]
            results = await asyncio.gather(*tasks)
        return "".join(results)

    except Exception as e:
        handle_exception(e, message="Failed to get web status", source="web")
        return f"Failed to get web status: {str(e)}"
