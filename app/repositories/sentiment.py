from datetime import date
from typing import Any

import duckdb

from app.repositories.base import PCT, fetch_all, fetch_one, paginate, where_clause
from app.schemas.common import Page, RankMetric, SortOrder

_METRIC_COL = {
    RankMetric.volume: "n_total",
    RankMetric.pct_positive: "pct_positive",
    RankMetric.pct_negative: "pct_negative",
}


# ------------------------------------------------------------------------- overall
def overall(db: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    return fetch_all(
        db,
        """
        SELECT sentiment, n_comments,
               100.0 * n_comments / SUM(n_comments) OVER () AS percentage
        FROM agg_overall_sentiment
        ORDER BY n_comments DESC
        """,
    )


def overall_summary(db: duckdb.DuckDBPyConnection) -> dict[str, Any] | None:
    return fetch_one(
        db,
        """
        SELECT SUM(n_comments) AS total_comments,
               SUM(n_comments) FILTER (WHERE sentiment = 'positive') AS n_positive,
               SUM(n_comments) FILTER (WHERE sentiment = 'negative') AS n_negative,
               SUM(n_comments) FILTER (WHERE sentiment = 'neutral')  AS n_neutral,
               SUM(n_comments) FILTER (WHERE sentiment = 'positive') * 1.0
                 / NULLIF(SUM(n_comments) FILTER (WHERE sentiment = 'negative'), 0)
                 AS positive_to_negative_ratio
        FROM agg_overall_sentiment
        """,
    )


# --------------------------------------------------------------------------- daily
# Rata-rata bergerak 7 baris terpusat (setara pandas rolling(7, center=True)); NULL di tepi.
_DAILY = f"""
    WITH d AS (
        SELECT comment_date, n_total, n_positive, n_negative, n_neutral, {PCT},
               CASE WHEN COUNT(*) OVER w = 7 THEN AVG(n_total) OVER w END AS n_total_ma7
        FROM agg_daily_sentiment
        WINDOW w AS (ORDER BY comment_date ROWS BETWEEN 3 PRECEDING AND 3 FOLLOWING)
    )
"""


def daily(
    db: duckdb.DuckDBPyConnection, start: date | None, end: date | None, order: SortOrder, page: Page
) -> tuple[list[dict[str, Any]], int]:
    conds, params = [], []
    if start:
        conds.append("comment_date >= ?")
        params.append(start)
    if end:
        conds.append("comment_date <= ?")
        params.append(end)
    select_sql = f"{_DAILY} SELECT * FROM d {where_clause(conds)}"
    return paginate(db, select_sql, params, f"comment_date {order.value}", page)


def daily_top(db: duckdb.DuckDBPyConnection, metric: RankMetric, limit: int, min_comments: int) -> list[dict[str, Any]]:
    col = _METRIC_COL[metric]
    return fetch_all(
        db,
        f"""{_DAILY}
        SELECT comment_date, n_total, pct_positive, pct_negative, pct_neutral
        FROM d WHERE n_total >= ?
        ORDER BY {col} DESC NULLS LAST, comment_date
        LIMIT ?""",
        [min_comments, limit],
    )


# ------------------------------------------------------------------------- monthly
_MONTHLY = f"""
    WITH m AS (
        SELECT month_start, n_total, n_positive, n_negative, n_neutral, {PCT}
        FROM agg_monthly_sentiment
    ), m2 AS (
        SELECT *,
               pct_positive - LAG(pct_positive) OVER (ORDER BY month_start) AS d_pct_positive_pp,
               pct_negative - LAG(pct_negative) OVER (ORDER BY month_start) AS d_pct_negative_pp,
               pct_neutral  - LAG(pct_neutral)  OVER (ORDER BY month_start) AS d_pct_neutral_pp
        FROM m
    )
"""


def monthly(
    db: duckdb.DuckDBPyConnection, start: date | None, end: date | None, order: SortOrder
) -> list[dict[str, Any]]:
    conds, params = [], []
    if start:
        conds.append("month_start >= ?")
        params.append(start)
    if end:
        conds.append("month_start <= ?")
        params.append(end)
    return fetch_all(
        db,
        f"{_MONTHLY} SELECT * FROM m2 {where_clause(conds)} ORDER BY month_start {order.value}",
        params,
    )


def monthly_top(db: duckdb.DuckDBPyConnection, metric: RankMetric, limit: int, min_comments: int) -> list[dict[str, Any]]:
    col = _METRIC_COL[metric]
    return fetch_all(
        db,
        f"""{_MONTHLY}
        SELECT month_start, n_total, pct_positive, pct_negative, pct_neutral
        FROM m2 WHERE n_total >= ?
        ORDER BY {col} DESC NULLS LAST, month_start
        LIMIT ?""",
        [min_comments, limit],
    )
