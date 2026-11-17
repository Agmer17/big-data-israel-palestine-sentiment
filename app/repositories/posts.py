from enum import StrEnum
from typing import Any

import duckdb

from app.repositories.base import PCT, fetch_all, fetch_one, paginate, where_clause
from app.schemas.common import Page, SortOrder

# balance_index: entropi Shannon (dinormalisasi ln(3)); 1 = sangat berimbang. Sama dengan notebook.
_POST_CTE = f"""
    WITH p AS (
        SELECT post_id, subreddit, post_title, post_score, post_upvote_ratio, post_created_time,
               n_total, n_positive, n_negative, n_neutral, {PCT},
               -( CASE WHEN n_positive > 0 THEN (n_positive * 1.0 / n_total) * ln(n_positive * 1.0 / n_total) ELSE 0 END
                + CASE WHEN n_negative > 0 THEN (n_negative * 1.0 / n_total) * ln(n_negative * 1.0 / n_total) ELSE 0 END
                + CASE WHEN n_neutral  > 0 THEN (n_neutral  * 1.0 / n_total) * ln(n_neutral  * 1.0 / n_total) ELSE 0 END
                 ) / ln(3) AS balance_index
        FROM agg_post_comment_sentiment
    )
"""


class PostMetric(StrEnum):
    volume = "volume"
    pct_negative = "pct_negative"
    pct_positive = "pct_positive"
    balance = "balance"


class PostSort(StrEnum):
    n_total = "n_total"
    pct_positive = "pct_positive"
    pct_negative = "pct_negative"
    pct_neutral = "pct_neutral"
    balance_index = "balance_index"
    post_score = "post_score"
    post_upvote_ratio = "post_upvote_ratio"
    post_created_time = "post_created_time"


_TOP_COL = {
    PostMetric.volume: "n_total",
    PostMetric.pct_negative: "pct_negative",
    PostMetric.pct_positive: "pct_positive",
    PostMetric.balance: "balance_index",
}
# Default min komentar mengikuti notebook (volume tanpa batas, lainnya >= 50).
DEFAULT_MIN = {PostMetric.volume: 0, PostMetric.pct_negative: 50, PostMetric.pct_positive: 50, PostMetric.balance: 50}


def top_posts(db: duckdb.DuckDBPyConnection, metric: PostMetric, limit: int, min_comments: int) -> list[dict[str, Any]]:
    col = _TOP_COL[metric]
    return fetch_all(
        db,
        f"{_POST_CTE} SELECT * FROM p WHERE n_total >= ? ORDER BY {col} DESC NULLS LAST, post_id LIMIT ?",
        [min_comments, limit],
    )


def list_posts(
    db: duckdb.DuckDBPyConnection,
    min_comments: int,
    subreddit: str | None,
    search: str | None,
    sort_by: PostSort,
    order: SortOrder,
    page: Page,
) -> tuple[list[dict[str, Any]], int]:
    conds, params = ["n_total >= ?"], [min_comments]
    if subreddit:
        conds.append("subreddit = ?")
        params.append(subreddit)
    if search:
        conds.append("post_title ILIKE ?")
        params.append(f"%{search}%")
    select_sql = f"{_POST_CTE} SELECT * FROM p {where_clause(conds)}"
    return paginate(db, select_sql, params, f"{sort_by.value} {order.value} NULLS LAST, post_id", page)


def comment_count_distribution(db: duckdb.DuckDBPyConnection, bins: int) -> dict[str, Any]:
    """Histogram log10(jumlah komentar per post), setara np.histogram(..., bins=bins)."""
    r = fetch_one(
        db,
        """
        SELECT MIN(log10(n_total)) AS lo, MAX(log10(n_total)) AS hi, COUNT(*) AS n_posts
        FROM agg_post_comment_sentiment WHERE n_total > 0
        """,
    )
    if not r or not r["n_posts"]:
        return {"bins": [], "n_posts": 0}
    lo, hi = r["lo"], r["hi"]
    if hi == lo:  # semua post punya jumlah komentar sama
        return {
            "n_posts": r["n_posts"],
            "bins": [{"bin_index": 0, "log10_start": lo, "log10_end": hi,
                      "comments_start": 10**lo, "comments_end": 10**hi, "n_posts": r["n_posts"]}],
        }
    width = (hi - lo) / bins
    counts = {
        row["bin_index"]: row["n_posts"]
        for row in fetch_all(
            db,
            """
            SELECT LEAST(CAST(FLOOR((log10(n_total) - ?) / ?) AS INTEGER), ? - 1) AS bin_index,
                   COUNT(*) AS n_posts
            FROM agg_post_comment_sentiment WHERE n_total > 0
            GROUP BY 1
            """,
            [lo, width, bins],
        )
    }
    out = []
    for i in range(bins):
        s, e = lo + i * width, lo + (i + 1) * width
        out.append({"bin_index": i, "log10_start": s, "log10_end": e,
                    "comments_start": 10**s, "comments_end": 10**e, "n_posts": counts.get(i, 0)})
    return {"n_posts": r["n_posts"], "bins": out}
