from fastapi import APIRouter

from app.core.database import DB
from app.repositories import users as repo
from app.schemas.common import ApiResponse, list_response

router = APIRouter(prefix="/users", tags=["3. Popularitas akun (karma) & karakteristik pengguna"])


@router.get("/karma/sentiment", summary="Sentimen per kategori karma (comment-weighted)")
def karma_sentiment(db: DB) -> ApiResponse:
    return list_response(repo.karma_sentiment(db))


@router.get("/karma/weighted-comparison", summary="Comment-weighted vs account-weighted per kategori karma")
def karma_weighted_comparison(db: DB) -> ApiResponse:
    return list_response(repo.karma_weighted_comparison(db))


@router.get("/account-age", summary="Sentimen berdasarkan usia akun")
def account_age(db: DB) -> ApiResponse:
    return list_response(repo.account_age(db))


@router.get("/verification", summary="Sentimen berdasarkan status verifikasi akun")
def verification(db: DB) -> ApiResponse:
    return list_response(repo.verification(db))
