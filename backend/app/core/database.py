from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


database_url = make_url(settings.DATABASE_URL)
connect_args = (
    {"check_same_thread": False}
    if database_url.get_backend_name() == "sqlite"
    else {}
)

engine = create_engine(
    database_url,
    connect_args=connect_args,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()