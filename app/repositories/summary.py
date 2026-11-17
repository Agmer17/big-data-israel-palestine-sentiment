from typing import Any

import duckdb

from app.repositories.base import fetch_all, fetch_one


def build_summary(db: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    """Padanan cell 'Rangkuman' notebook: semua angka dihitung dari tabel agregasi."""
    dominant = fetch_one(
        db,
        """
        SELECT sentiment, n_comments, 100.0 * n_comments / SUM(n_comments) OVER () AS percentage
        FROM agg_overall_sentiment ORDER BY n_comments DESC LIMIT 1
        """,
    )
    ratio = fetch_one(
        db,
        """
        SELECT SUM(n_comments) FILTER (WHERE sentiment = 'positive') * 1.0
               / NULLIF(SUM(n_comments) FILTER (WHERE sentiment = 'negative'), 0) AS r
        FROM agg_overall_sentiment
        """,
    )
    if dominant is not None:
        dominant["positive_to_negative_ratio"] = ratio["r"] if ratio else None

    busiest_day = fetch_one(db, "SELECT comment_date, n_total FROM agg_daily_sentiment ORDER BY n_total DESC LIMIT 1")
    busiest_month = fetch_one(db, "SELECT month_start, n_total FROM agg_monthly_sentiment ORDER BY n_total DESC LIMIT 1")
    most_negative_month = fetch_one(
        db,
        """SELECT month_start, 100.0 * n_negative / n_total AS pct_negative FROM agg_monthly_sentiment
           WHERE n_total >= 1000 ORDER BY 2 DESC LIMIT 1""",
    )
    most_positive_month = fetch_one(
        db,
        """SELECT month_start, 100.0 * n_positive / n_total AS pct_positive FROM agg_monthly_sentiment
           WHERE n_total >= 1000 ORDER BY 2 DESC LIMIT 1""",
    )

    largest_subreddits = fetch_all(
        db,
        """SELECT subreddit, n_total, 100.0 * n_total / SUM(n_total) OVER () AS pct_of_all_comments
           FROM agg_subreddit_sentiment ORDER BY n_total DESC LIMIT 3""",
    )
    highest_neg = fetch_one(
        db,
        """SELECT subreddit, 100.0 * n_negative / n_total AS pct_negative FROM agg_subreddit_sentiment
           WHERE n_total >= 100 ORDER BY 2 DESC LIMIT 1""",
    )
    lowest_neg = fetch_one(
        db,
        """SELECT subreddit, 100.0 * n_negative / n_total AS pct_negative FROM agg_subreddit_sentiment
           WHERE n_total >= 100 ORDER BY 2 ASC LIMIT 1""",
    )

    karma = fetch_all(
        db,
        """
        SELECT k.karma_category, k.n_total,
               100.0 * k.n_negative / NULLIF(k.n_total, 0) AS comment_weighted_pct_negative,
               100.0 * a.sum_prop_negative / NULLIF(a.n_accounts, 0) AS account_weighted_pct_negative
        FROM agg_karma_sentiment k
        JOIN agg_account_weighted_sentiment a ON k.category_order = a.category_order
        ORDER BY k.category_order
        """,
    )
    engagement = fetch_all(
        db,
        """
        SELECT sentiment,
               SUM(sum_score) * 1.0 / NULLIF(SUM(n_score), 0) AS avg_score,
               SUM(sum_ups)   * 1.0 / NULLIF(SUM(n_ups), 0)   AS avg_ups,
               SUM(sum_downs) * 1.0 / NULLIF(SUM(n_downs), 0) AS avg_downs
        FROM agg_comment_score_sentiment GROUP BY sentiment ORDER BY sentiment
        """,
    )
    biggest_post = fetch_one(
        db,
        """
        SELECT post_id, subreddit, left(post_title, 80) AS post_title, n_total,
               100.0 * n_negative / NULLIF(n_total, 0) AS pct_negative
        FROM agg_post_comment_sentiment ORDER BY n_total DESC LIMIT 1
        """,
    )
    keywords = fetch_all(
        db,
        """
        SELECT keyword, SUM(n_occurrences) AS n_occurrences
        FROM agg_keyword_sentiment WHERE source_field = 'comment'
        GROUP BY keyword ORDER BY n_occurrences DESC LIMIT 10
        """,
    )
    associations = fetch_all(db, "SELECT analysis, cramers_v FROM agg_association_stats ORDER BY cramers_v DESC")

    return {
        "dominant_sentiment": dominant,
        "peak_activity": {
            "busiest_day": busiest_day,
            "busiest_month": busiest_month,
            "most_negative_month": most_negative_month,
            "most_positive_month": most_positive_month,
        },
        "subreddits": {
            "largest": largest_subreddits,
            "highest_pct_negative": highest_neg,
            "lowest_pct_negative": lowest_neg,
        },
        "karma_negative_by_category": karma,
        "engagement_by_sentiment": engagement,
        "largest_discussion_post": biggest_post,
        "top_comment_keywords": [k["keyword"] for k in keywords],
        "association_strength": associations,
    }
