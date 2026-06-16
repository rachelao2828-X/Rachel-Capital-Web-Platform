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
    _ensure_sqlite_sync_columns()


def _ensure_sqlite_sync_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    required_columns = {
        "obsidian_sync": "VARCHAR(50) NOT NULL DEFAULT 'skipped'",
        "git_sync": "VARCHAR(50) NOT NULL DEFAULT 'skipped'",
        "obsidian_path": "TEXT",
        "last_synced_at": "DATETIME",
    }
    with engine.begin() as connection:
        existing_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(news_items)").fetchall()
        }
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                connection.exec_driver_sql(
                    f"ALTER TABLE news_items ADD COLUMN {column_name} {column_type}"
                )


def session_scope() -> Session:
    return SessionLocal()
