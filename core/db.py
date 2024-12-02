from sqlmodel import Session, create_engine

from core.config import MYSQL_URL

engine = create_engine(MYSQL_URL)


def get_session():
    with Session(engine) as session:
        yield session
