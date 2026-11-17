from typing import Any

import duckdb

from app.repositories.base import fetch_all


def score_distribution(db: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    return fetch_all(
        db,
        """
        SELECT score_category, category_order,
               SUM(n_comments) AS n_comments,
               100.0 * SUM(n_comments) / SUM(SUM(n_comments)) OVER () AS percentage
        FROM agg_comment_score_sentiment
        GROUP BY score_category, category_order
        ORDER BY category_order
        """,
    )


def by_sentiment(db: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    """Rata-rata score/ups/downs per sentimen (dihitung dari sum/count seperti di notebook)."""
    return fetch_all(
        db,
        """
        SELECT sentiment,
               SUM(n_comments) AS n_comments,
               SUM(sum_score) * 1.0 / NULLIF(SUM(n_score), 0) AS avg_score,
               SUM(sum_ups)   * 1.0 / NULLIF(SUM(n_ups), 0)   AS avg_ups,
               SUM(sum_downs) * 1.0 / NULLIF(SUM(n_downs), 0) AS avg_downs
        FROM agg_comment_score_sentiment
        GROUP BY sentiment
        ORDER BY n_comments DESC
        """,
    )


def score_category_sentiment(db: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    return fetch_all(
        db,
        """
        SELECT score_category, category_order,
               SUM(n_comments) AS n_comments,
               100.0 * SUM(n_comments) FILTER (WHERE sentiment = 'positive') / NULLIF(SUM(n_comments), 0) AS pct_positive,
               100.0 * SUM(n_comments) FILTER (WHERE sentiment = 'negative') / NULLIF(SUM(n_comments), 0) AS pct_negative,
               100.0 * SUM(n_comments) FILTER (WHERE sentiment = 'neutral')  / NULLIF(SUM(n_comments), 0) AS pct_neutral
        FROM agg_comment_score_sentiment
        GROUP BY score_category, category_order
        ORDER BY category_order
        """,
    )


def controversiality(db: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    return fetch_all(
        db,
        """
        SELECT controversiality,
               SUM(n_comments) AS n_comments,
               100.0 * SUM(n_comments) FILTER (WHERE sentiment = 'positive') / NULLIF(SUM(n_comments), 0) AS pct_positive,
               100.0 * SUM(n_comments) FILTER (WHERE sentiment = 'negative') / NULLIF(SUM(n_comments), 0) AS pct_negative,
               100.0 * SUM(n_comments) FILTER (WHERE sentiment = 'neutral')  / NULLIF(SUM(n_comments), 0) AS pct_neutral
        FROM agg_controversiality_sentiment
        GROUP BY controversiality
        ORDER BY controversiality
        """,
    )


def controversial_share_by_sentiment(db: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    return fetch_all(
        db,
        """
        SELECT sentiment,
               100.0 * SUM(n_comments) FILTER (WHERE controversiality = 1) / NULLIF(SUM(n_comments), 0) AS pct_controversial
        FROM agg_controversiality_sentiment
        GROUP BY sentiment
        ORDER BY sentiment
        """,
    )
