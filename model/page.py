from sqlmodel import SQLModel, Field
from sqlalchemy import TEXT


class Page(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    content: str = Field(sa_type=TEXT)

