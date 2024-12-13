from core.redis import redis_client


async def set_access_granted_user(user_id):
    """Add user to access granted list"""
    return redis_client.sadd("user", str(user_id))


async def set_cf_node(data: str):
    """Set CF nodes"""
    nodes = data.strip().split(";")
    return redis_client.sadd("cf_node", *nodes)


async def set_path(data: str):
    """Set paths"""
    path = {}
    for item in data.strip().split(";"):
        key, value = item.split("-", 1)
        path[key] = value
    return redis_client.hset("path", mapping=path)


async def set_alive_url(url: list):
    """Set alive URL"""
    url = url.strip().split(";")
    return redis_client.sadd("alive", *url)


async def set_deploy_url(url: str):
    """Set deploy URL"""
    return redis_client.set("deploy_url", url)
