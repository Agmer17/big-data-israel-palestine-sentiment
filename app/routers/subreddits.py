from fastapi import APIRouter, Depends, Query

from app.core.database import DB
from app.repositories import subreddits as repo
from app.repositories.subreddits import SubredditSort
from app.schemas.common import (
    ApiResponse, Page, RankMetric, SortOrder, list_response, pagination_params, paginated_meta,
)

router = APIRouter(prefix="/subreddits", tags=["2. Subreddit"])


@router.get("", summary="Daftar subreddit + distribusi sentimen (paginasi)")
def list_subreddits(
    db: DB,
    min_comments: int = Query(100, ge=0, description="Minimal komentar (default notebook: 100)."),
    search: str | None = Query(None, min_length=1, max_length=100, description="Cari nama subreddit (contains, case-insensitive)."),
    sort_by: SubredditSort = SubredditSort.n_total,
    order: SortOrder = SortOrder.desc,
    page: Page = Depends(pagination_params(default_size=50, max_size=500)),
) -> ApiResponse:
    rows, total = repo.list_subreddits(db, min_comments, search, sort_by, order, page)
    return ApiResponse(data=rows, meta=paginated_meta(total, page))


@router.get("/top", summary="Top subreddit berdasarkan volume / % positif / % negatif")
def top_subreddits(
    db: DB,
    metric: RankMetric = RankMetric.volume,
    limit: int = Query(10, ge=1, le=100),
    min_comments: int = Query(100, ge=0),
) -> ApiResponse:
    return list_response(repo.top_subreddits(db, metric, limit, min_comments), metric=metric, min_comments=min_comments)
