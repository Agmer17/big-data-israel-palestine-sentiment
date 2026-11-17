from fastapi import APIRouter, Depends, Query

from app.core.database import DB
from app.repositories import posts as repo
from app.repositories.posts import DEFAULT_MIN, PostMetric, PostSort
from app.schemas.common import (
    ApiResponse, Page, SortOrder, list_response, pagination_params, paginated_meta,
)

router = APIRouter(prefix="/posts", tags=["5. Analisis topik post"])


@router.get("", summary="Daftar post + sentimen komentarnya (paginasi)")
def list_posts(
    db: DB,
    min_comments: int = Query(1, ge=0),
    subreddit: str | None = Query(None, max_length=100, description="Filter subreddit (exact match)."),
    search: str | None = Query(None, min_length=1, max_length=100, description="Cari di judul post."),
    sort_by: PostSort = PostSort.n_total,
    order: SortOrder = SortOrder.desc,
    page: Page = Depends(pagination_params(default_size=20, max_size=100)),
) -> ApiResponse:
    rows, total = repo.list_posts(db, min_comments, subreddit, search, sort_by, order, page)
    return ApiResponse(data=rows, meta=paginated_meta(total, page))


@router.get("/top", summary="Top post: diskusi terbanyak / paling negatif / paling positif / paling berimbang")
def top_posts(
    db: DB,
    metric: PostMetric = PostMetric.volume,
    limit: int = Query(10, ge=1, le=100),
    min_comments: int | None = Query(None, ge=0, description="Default notebook: 0 untuk volume, 50 untuk metrik lain."),
) -> ApiResponse:
    if min_comments is None:
        min_comments = DEFAULT_MIN[metric]
    return list_response(repo.top_posts(db, metric, limit, min_comments), metric=metric, min_comments=min_comments)


@router.get("/comment-count-distribution", summary="Histogram log10(jumlah komentar per post)")
def comment_count_distribution(db: DB, bins: int = Query(40, ge=1, le=200)) -> ApiResponse:
    result = repo.comment_count_distribution(db, bins)
    return ApiResponse(data=result["bins"], meta={"total": len(result["bins"]), "n_posts": result["n_posts"]})
