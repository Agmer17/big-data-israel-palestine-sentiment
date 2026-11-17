from enum import StrEnum
from typing import Any

import duckdb

from app.repositories.base import PCT, fetch_all, paginate, where_clause
from app.schemas.common import Page, RankMetric, SortOrder


class SubredditSort(StrEnum):
    n_total = "n_total"
    pct_positive = "pct_positive"
    pct_negative = "pct_negative"
    pct_neutral = "pct_neutral"
    avg_score = "avg_score"
    n_posts = "n_posts"
    subreddit = "subreddit"


_BASE = f"""
    SELECT subreddit, n_total, n_positive, n_negative, n_neutral, {PCT},
           sum_score * 1.0 / NULLIF(n_score, 0) AS avg_score,
           n_posts
    FROM agg_subreddit_sentiment
"""
_METRIC_COL = {
    RankMetric.volume: "n_total",
    RankMetric.pct_positive: "pct_positive",
    RankMetric.pct_negative: "pct_negative",
}


def list_subreddits(
    db: duckdb.DuckDBPyConnection,
    min_comments: int,
    search: str | None,
    sort_by: SubredditSort,
    order: SortOrder,
    page: Page,
) -> tuple[list[dict[str, Any]], int]:
    conds, params = ["n_total >= ?"], [min_comments]
    if search:
        conds.append("subreddit ILIKE ?")
        params.append(f"%{search}%")
    select_sql = f"SELECT * FROM ({_BASE}) WHERE subreddit IS NOT NULL AND {' AND '.join(conds)}"
    return paginate(db, select_sql, params, f"{sort_by.value} {order.value} NULLS LAST, subreddit", page)


def top_subreddits(db: duckdb.DuckDBPyConnection, metric: RankMetric, limit: int, min_comments: int) -> list[dict[str, Any]]:
    col = _METRIC_COL[metric]
    return fetch_all(
        db,
        f"SELECT * FROM ({_BASE}) WHERE n_total >= ? ORDER BY {col} DESC NULLS LAST, subreddit LIMIT ?",
        [min_comments, limit],
    )
