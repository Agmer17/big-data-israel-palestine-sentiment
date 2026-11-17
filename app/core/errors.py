import logging
from typing import Any

import duckdb
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.serialization import sanitize

logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: Any = None) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


def _body(code: str, message: str, details: Any = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": sanitize(details)}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(_body(exc.code, exc.message, exc.details), status_code=exc.status_code)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        return JSONResponse(_body(code, str(exc.detail)), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            _body("validation_error", "Parameter request tidak valid.", details), status_code=422
        )

    @app.exception_handler(duckdb.CatalogException)
    async def _catalog_error(_: Request, exc: duckdb.CatalogException) -> JSONResponse:
        logger.error("Tabel/kolom tidak ditemukan: %s", exc)
        return JSONResponse(
            _body("analysis_table_missing", "Tabel agregasi yang dibutuhkan tidak ada di database."),
            status_code=503,
        )

    @app.exception_handler(duckdb.Error)
    async def _duckdb_error(_: Request, exc: duckdb.Error) -> JSONResponse:
        logger.exception("DuckDB error: %s", exc)
        return JSONResponse(_body("database_error", "Terjadi kesalahan pada database."), status_code=500)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(_body("internal_error", "Terjadi kesalahan internal."), status_code=500)
