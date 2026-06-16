from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.news import router as news_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db.session import init_db

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(news_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "status": "initialized",
        "phase": "daily_intelligence_mvp",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
