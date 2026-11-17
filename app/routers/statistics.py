from fastapi import APIRouter

from app.core.database import DB
from app.repositories import statistics as repo
from app.repositories.statistics import ContingencyVariable
from app.schemas.common import ApiResponse, list_response

router = APIRouter(prefix="/statistics", tags=["7. Uji statistik & asosiasi"])


@router.get("/associations", summary="Hasil uji chi-square & Cramér's V tiap variabel vs sentimen")
def associations(db: DB) -> ApiResponse:
    return list_response(repo.associations(db))


@router.get("/contingency", summary="Tabel kontingensi variabel vs sentimen (jumlah + persen baris)")
def contingency(db: DB, variable: ContingencyVariable) -> ApiResponse:
    return list_response(repo.contingency(db, variable), variable=variable)
