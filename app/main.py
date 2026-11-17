import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.constants import REQUIRED_TABLES
from app.core.config import get_settings
from app.core.database import Database
from app.core.errors import register_exception_handlers
from app.routers import engagement, keywords, posts, statistics, subreddits, summary, system, users
from app.routers import sentiment
from app.schemas.common import SafeJSONResponse

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    db = Database(settings.duckdb_path)
    db.open()  # gagal cepat dengan pesan jelas kalau file tidak ada
    missing = [t for t in REQUIRED_TABLES if t not in db.existing_tables()]
    if missing:
        logger.warning("Tabel agregasi berikut tidak ditemukan di database: %s", ", ".join(missing))
    app.state.db = db
    try:
        yield
    finally:
        db.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="REST API read-only untuk hasil agregasi & analisis sentimen Reddit (DuckDB).",
        lifespan=lifespan,
        default_response_class=SafeJSONResponse,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    api = APIRouter(prefix="/api")
    api.include_router(system.router)

    analytics = APIRouter(prefix="/analytics")
    for r in (sentiment.router, subreddits.router, users.router, engagement.router,
              posts.router, keywords.router, statistics.router, summary.router):
        analytics.include_router(r)
    api.include_router(analytics)

    app.include_router(api)
    return app


app = create_app()
