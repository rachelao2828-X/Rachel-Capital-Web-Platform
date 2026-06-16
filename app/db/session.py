from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base


def _create_engine() -> Engine:
    connect_args = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        database_path = settings.database_url.replace("sqlite:///", "", 1)
        if database_path and database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)

    return create_engine(settings.database_url, connect_args=connect_args, future=True)


engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models before creating tables so SQLAlchemy metadata is complete.
    from app.models import news  # noqa: F401

    Base.metadata.create_all(bind=engine)


def session_scope() -> Session:
    return SessionLocal()

