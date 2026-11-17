from enum import StrEnum

from fastapi import APIRouter, Depends, Query

from app.constants import THEMES
from app.core.database import DB
from app.core.errors import ApiError
from app.repositories import keywords as repo
from app.schemas.common import (
    ApiResponse, Page, Sentiment, list_response, pagination_params, paginated_meta,
)

router = APIRouter(prefix="/keywords", tags=["6. Keyword & topik"])


class SourceField(StrEnum):
    comment = "comment"
    post_title = "post_title"
    post_body = "post_body"


class Direction(StrEnum):
    negative = "negative"
    positive = "positive"


@router.get("/top", summary="Top keyword (komentar / judul post / isi post)")
def top_keywords(
    db: DB,
    source_field: SourceField = SourceField.comment,
    sentiment: Sentiment | None = Query(None, description="Hanya untuk source_field=comment."),
    page: Page = Depends(pagination_params(default_size=20, max_size=100)),
) -> ApiResponse:
    if sentiment and source_field != SourceField.comment:
        raise ApiError(422, "invalid_filter", "Filter sentiment hanya berlaku untuk source_field=comment.")
    rows, total = repo.top_keywords(db, source_field.value, sentiment.value if sentiment else None, page)
    return ApiResponse(data=rows, meta=paginated_meta(total, page))


@router.get("/distinctive", summary="Keyword paling khas untuk satu sentimen (smoothed log2 ratio)")
def distinctive(
    db: DB,
    sentiment: Sentiment,
    limit: int = Query(15, ge=1, le=100),
    min_occurrences: int = Query(20, ge=1, description="Minimal kemunculan pada sentimen tsb (default notebook: 20)."),
) -> ApiResponse:
    rows = repo.distinctive_keywords(db, sentiment.value, min_occurrences, limit)
    return list_response(rows, sentiment=sentiment, min_occurrences=min_occurrences)


@router.get("/negative-vs-positive", summary="Keyword lebih khas di komentar negatif vs positif")
def negative_vs_positive(
    db: DB,
    direction: Direction = Direction.negative,
    limit: int = Query(15, ge=1, le=100),
    min_occurrences: int = Query(20, ge=1, description="Minimal kemunculan di kedua kelas (default notebook: 20)."),
) -> ApiResponse:
    rows = repo.negative_vs_positive(db, direction.value, min_occurrences, limit)
    return list_response(rows, direction=direction, min_occurrences=min_occurrences)


@router.get("/themes", summary="Intensitas tema (per 10.000 token) berdasarkan sentimen")
def themes(db: DB) -> ApiResponse:
    return list_response(repo.themes(db))


@router.get("/themes/definitions", summary="Daftar keyword penyusun tiap tema")
def theme_definitions() -> ApiResponse:
    data = [{"theme": t, "keywords": kws} for t, kws in THEMES.items()]
    return list_response(data)
