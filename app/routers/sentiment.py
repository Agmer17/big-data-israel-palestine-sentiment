from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.database import DB
from app.core.errors import ApiError
from app.repositories import sentiment as repo
from app.schemas.common import (
    ApiResponse, Page, RankMetric, SortOrder, list_response, pagination_params, paginated_meta,
)

router = APIRouter(prefix="/sentiment", tags=["1. Sentimen keseluruhan & temporal"])


def _check_range(start: date | None, end: date | None) -> None:
    if start and end and start > end:
        raise ApiError(422, "invalid_date_range", "Parameter start harus lebih kecil atau sama dengan end.")


@router.get("/overall", summary="Distribusi sentimen keseluruhan")
def overall(db: DB) -> ApiResponse:
    return list_response(repo.overall(db))


@router.get("/overall/summary", summary="Ringkasan total komentar & rasio positif:negatif")
def overall_summary(db: DB) -> ApiResponse:
    return ApiResponse(data=repo.overall_summary(db))


@router.get("/daily", summary="Tren sentimen harian (paginasi)")
def daily(
    db: DB,
    start_date: date | None = Query(None, description="Tanggal awal (YYYY-MM-DD), inklusif."),
    end_date: date | None = Query(None, description="Tanggal akhir (YYYY-MM-DD), inklusif."),
    order: SortOrder = SortOrder.asc,
    page: Page = Depends(pagination_params(default_size=100, max_size=1000)),
) -> ApiResponse:
    _check_range(start_date, end_date)
    rows, total = repo.daily(db, start_date, end_date, order, page)
    return ApiResponse(data=rows, meta=paginated_meta(total, page))


@router.get("/daily/top", summary="Top hari berdasarkan volume / % positif / % negatif")
def daily_top(
    db: DB,
    metric: RankMetric = RankMetric.volume,
    limit: int = Query(5, ge=1, le=100),
    min_comments: int | None = Query(
        None, ge=0, description="Minimal komentar per hari. Default notebook: 0 untuk volume, 100 untuk metrik persentase."
    ),
) -> ApiResponse:
    if min_comments is None:
        min_comments = 0 if metric == RankMetric.volume else 100
    return list_response(repo.daily_top(db, metric, limit, min_comments), metric=metric, min_comments=min_comments)


@router.get("/monthly", summary="Tren sentimen bulanan + perubahan antar bulan (poin persentase)")
def monthly(
    db: DB,
    start_month: date | None = Query(None, description="Bulan awal (YYYY-MM-DD, tanggal 1 bulan tsb)."),
    end_month: date | None = Query(None, description="Bulan akhir (YYYY-MM-DD)."),
    order: SortOrder = SortOrder.asc,
) -> ApiResponse:
    _check_range(start_month, end_month)
    return list_response(repo.monthly(db, start_month, end_month, order))


@router.get("/monthly/top", summary="Top bulan berdasarkan volume / % positif / % negatif")
def monthly_top(
    db: DB,
    metric: RankMetric = RankMetric.volume,
    limit: int = Query(5, ge=1, le=100),
    min_comments: int | None = Query(
        None, ge=0, description="Minimal komentar per bulan. Default notebook: 0 untuk volume, 1000 untuk metrik persentase."
    ),
) -> ApiResponse:
    if min_comments is None:
        min_comments = 0 if metric == RankMetric.volume else 1000
    return list_response(repo.monthly_top(db, metric, limit, min_comments), metric=metric, min_comments=min_comments)
