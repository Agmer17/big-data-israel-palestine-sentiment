from fastapi import APIRouter

from app.core.database import DB
from app.repositories import engagement as repo
from app.schemas.common import ApiResponse, list_response

router = APIRouter(prefix="/engagement", tags=["4. Engagement komentar"])


@router.get("/score-distribution", summary="Distribusi kategori score komentar")
def score_distribution(db: DB) -> ApiResponse:
    return list_response(repo.score_distribution(db))


@router.get("/by-sentiment", summary="Rata-rata score, upvotes, downvotes per sentimen")
def by_sentiment(db: DB) -> ApiResponse:
    return list_response(repo.by_sentiment(db))


@router.get("/score-category-sentiment", summary="Komposisi sentimen per kategori score")
def score_category_sentiment(db: DB) -> ApiResponse:
    return list_response(repo.score_category_sentiment(db))


@router.get("/controversiality", summary="Komposisi sentimen berdasarkan controversiality (0/1)")
def controversiality(db: DB) -> ApiResponse:
    return list_response(repo.controversiality(db))


@router.get("/controversiality/by-sentiment", summary="% komentar kontroversial per sentimen")
def controversial_share(db: DB) -> ApiResponse:
    return list_response(repo.controversial_share_by_sentiment(db))
