from fastapi import APIRouter

from app.core.database import DB
from app.repositories import summary as repo
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/summary", tags=["8. Rangkuman / key insights"])


@router.get("", summary="Key insights yang dihitung dari tabel agregasi (padanan cell Rangkuman)")
def summary(db: DB) -> ApiResponse:
    return ApiResponse(data=repo.build_summary(db))
