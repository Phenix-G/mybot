from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import TEXT


class Page(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    url: Optional[str] = None
    content: str = Field(sa_type=TEXT, nullable=True)
