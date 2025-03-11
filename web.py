import asyncio
from contextlib import asynccontextmanager
import logging
import random
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Depends, Response, HTTPException
from fastapi.responses import JSONResponse
import httpx
from sqlmodel import Session, select

from bot import TelegramBot
from core.config import INTERVAL_TIME, WEB_PORT
from core.db import get_session
from core.exceptions import handle_exception
from core.redis import redis_client
from core.utils import send_message
from model.page import Page

stop_web_event = asyncio.Event()
restart_lock = Lock()

cache_page = "Hello, World!"


# Initialize scheduler
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start scheduler and add scheduled tasks
    scheduler.add_job(keep_web_alive, "interval", seconds=INTERVAL_TIME)

    scheduler.start()

    yield  # Application runs here until shutdown

    # Cleanup on application shutdown
    scheduler.shutdown()


def keep_web_alive():
    """Keep web service alive by periodic health checks"""
    # Check stop event
    if stop_web_event.is_set():
        return

    try:
        httpx.get(f"http://127.0.0.1:{WEB_PORT}/")
    except Exception as e:
        handle_exception(e, "Error: {e}", source="keep_web_alive")


# Add a new function to handle shutdown
def shutdown_scheduler():
    if scheduler.running:
        try:
            scheduler.shutdown(wait=False)
            logging.info("Scheduler shutdown completed")
        except Exception as e:
            handle_exception(e, "Error shutting down scheduler", source="scheduler")


app = FastAPI(lifespan=lifespan, openapi_url=None)


@app.get("/")
async def index(name: str | None = None, session: Session = Depends(get_session)):
    """Get page content by name or return a random page"""
    try:
        if name:
            return await get_page_by_name(name, session)
        return await get_random_page(session)
    except Exception as e:
        handle_exception(e, "Failed to get page content", source="web")
        return Response(
            content=f"Error: {str(e)}", media_type="text/html", status_code=500
        )


async def get_page_by_name(name: str, session: Session) -> Response:
    """Get page content by name"""
    page = session.exec(select(Page).where(Page.name == name)).first()
    if not page:
        return Response(
            content="Page not found", media_type="text/html", status_code=404
        )

    cache_page = page.content
    return Response(content=cache_page, media_type="text/html")


async def get_random_page(session: Session) -> Response:
    """Get a random page from database or Redis"""

    # Get pages from database
    db_pages = [i.content for i in session.exec(select(Page)).all()]

    # Get pages from Redis
    # redis_pages = redis_client.smembers("page")
    redis_pages = []

    # Combine pages
    all_pages = db_pages + list(redis_pages)
    if not all_pages:
        return Response(
            content="No pages available", media_type="text/html", status_code=404
        )

    # Select random page
    page = random.choice(all_pages)
    try:
        index_page = page.content if hasattr(page, "content") else page
    except AttributeError:
        index_page = page

    return Response(content=index_page, media_type="text/html")


@app.get("/telegram")
async def telegram(bot_token: str, chat_id: str, message: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    params = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": "true",
    }

    response = httpx.get(url, headers=headers, params=params)
    return JSONResponse(content=response.json())


@app.get("/alive")
async def alive(urls: list[str]):
    """Check if the web service is alive"""
    results = []
    for url in urls:
        try:
            response = httpx.get(url)
            if response.status_code != 200:
                results.append({f"{url}": "failed", "message": str(e)})
            else:
                results.append({f"{url}": "success"})
        except Exception as e:
            results.append({f"{url}": "failed", "message": str(e)})
    return JSONResponse(content=results)


@app.get("/restart")
async def restart(uuid: str):
    """Restart the program"""
    global restart_lock
    restart_uuid = redis_client.get("restart_uuid")
    if uuid != restart_uuid:
        raise HTTPException(status_code=403, detail="Invalid UUID")

    # Use restart lock to prevent concurrent restarts
    if not restart_lock.acquire(blocking=False):
        logging.warning("Restart already in progress")
        raise HTTPException(status_code=400, detail="Restart already in progress")

    try:
        bot = TelegramBot()
        # Check bot status before restart
        if bot.is_running:
            bot.thread_stop()

        # Start new bot instance
        bot.thread_start()

        logging.info("Bot has been restarted successfully")
        return Response(content="Bot restarted successfully", media_type="text/html")
    except Exception as e:
        restart_lock.release()
        handle_exception(
            e, "Failed to restart bot", source="web", notify_func=send_message
        )
        raise HTTPException(status_code=500, detail=f"Failed to restart: {str(e)}")
    finally:
        restart_lock.release()


@app.get("/node")
async def get_node():
    """Get node"""
    result = redis_client.hgetall("node")
    return JSONResponse({"status": "success", "result": result})


@app.post("/node")
async def create_node(name: str, node: str):
    """Set node"""
    result = redis_client.hset("node", mapping={name: node})
    return JSONResponse({"status": "success", "result": result})


@app.put("/node")
async def update_node(name: str, node: str):
    """Update node"""
    result = redis_client.hset("node", mapping={name: node})
    return JSONResponse({"status": "success", "result": result})


@app.delete("/node")
async def delete_node(name: str):
    """Delete node"""
    result = redis_client.hdel("node", name)
    return JSONResponse({"status": "success", "result": result})


@app.get("/page")
async def get_page():
    """Get page"""
    result = redis_client.hgetall("page")
    return JSONResponse({"status": "success", "result": result})
