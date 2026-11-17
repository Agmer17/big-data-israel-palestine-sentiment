from fastapi import APIRouter, Request

from app.constants import REQUIRED_TABLES
from app.core.database import DB
from app.repositories import system as repo
from app.schemas.common import ApiResponse, list_response

router = APIRouter(tags=["0. Sistem"])


@router.get("/health", summary="Cek koneksi database & kelengkapan tabel")
def health(request: Request) -> ApiResponse:
    existing = request.app.state.db.existing_tables()
    missing = [t for t in REQUIRED_TABLES if t not in existing]
    return ApiResponse(data={"status": "ok" if not missing else "degraded", "database_connected": True,
                             "missing_tables": missing})


@router.get("/meta/tables", summary="Daftar tabel agregasi + jumlah baris")
def tables(db: DB) -> ApiResponse:
    return list_response(repo.table_row_counts(db))
