from typing import Tuple
import re

import httpx
from sqlmodel import select

from core.exceptions import handle_exception
from core.db import get_session
from core.redis import redis_client
from model.page import Page


def parse_page_data(data: str) -> Tuple[str, str]:
    """Parse page data from string format"""
    try:
        name, content = data.strip().split("-", 1)
        return name, content
    except ValueError as e:
        handle_exception(e, "Invalid page data format", source="parse_page_data")
        raise ValueError("Data must be in format 'name-content'")


async def fetch_page_content(url: str):
    """Fetch page content from URL"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except Exception as e:
        handle_exception(e, "Failed to fetch page content", source="fetch_page_content")
        return None


# @handle_db_error
# @handle_redis_error
async def set_page(data: str):
    """Set page content in database and Redis"""
    name, content = parse_page_data(data)

    session = next(get_session())
    page = session.exec(select(Page).where(Page.name == name)).first()

    try:
        if re.match(r"https?://", content):
            page_content = await fetch_page_content(content)
            redis_client.sadd("page", content)

            if page:
                page.url = content
                page.content = page_content
            else:
                page = Page(name=name, url=content, content=page_content)

        else:
            if page:
                page.content = content
            else:
                page = Page(name=name, content=content)

        session.add(page)
        session.commit()

    except Exception as e:
        session.rollback()
        handle_exception(e, "Failed to set page", source="page")
        raise
    finally:
        session.close()


def get_pages():
    """Get all pages"""
    session = next(get_session())
    try:
        pages = session.exec(select(Page)).all()
        result = ";".join([f"{p.name}" for p in pages])
        return f"pages: {result}"
    finally:
        session.close()
