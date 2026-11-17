import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Callable

from fastapi import Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.utils.serialization import sanitize


class SafeJSONResponse(JSONResponse):
    """JSONResponse yang menjamin tidak ada NaN/Infinity di body."""

    def render(self, content: Any) -> bytes:
        return super().render(sanitize(content))


class ApiResponse(BaseModel):
    """Envelope standar semua endpoint: {"data": ..., "meta": {...}}."""

    data: Any
    meta: dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------------------------------- enums
class SortOrder(StrEnum):
    asc = "asc"
    desc = "desc"


class Sentiment(StrEnum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"


class RankMetric(StrEnum):
    volume = "volume"
    pct_positive = "pct_positive"
    pct_negative = "pct_negative"


# ----------------------------------------------------------------------- pagination
@dataclass(frozen=True)
class Page:
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def pagination_params(default_size: int = 50, max_size: int = 500) -> Callable[..., Page]:
    def dep(
        page: int = Query(1, ge=1, description="Nomor halaman (mulai dari 1)."),
        page_size: int = Query(
            default_size, ge=1, le=max_size, description=f"Jumlah item per halaman (maks {max_size})."
        ),
    ) -> Page:
        return Page(page=page, page_size=page_size)

    return dep


def paginated_meta(total: int, p: Page) -> dict[str, Any]:
    return {
        "total": total,
        "page": p.page,
        "page_size": p.page_size,
        "total_pages": math.ceil(total / p.page_size) if total else 0,
    }


def list_response(rows: list[dict[str, Any]], **extra: Any) -> ApiResponse:
    return ApiResponse(data=rows, meta={"total": len(rows), **extra})
