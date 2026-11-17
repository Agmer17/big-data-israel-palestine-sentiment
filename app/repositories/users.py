from typing import Any

import duckdb

from app.repositories.base import PCT, fetch_all


def karma_sentiment(db: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    """Comment-weighted: tiap komentar dihitung sama."""
    return fetch_all(
        db,
        f"""
        SELECT karma_category, category_order, n_total, n_positive, n_negative, n_neutral,
               {PCT},
               sum_score * 1.0 / NULLIF(n_score, 0) AS avg_score,
               n_accounts
        FROM agg_karma_sentiment
        ORDER BY category_order
        """,
    )


def karma_weighted_comparison(db: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    """Perbandingan comment-weighted (cw) vs account-weighted (aw)."""
    return fetch_all(
        db,
        """
        SELECT k.karma_category, k.category_order,
               100.0 * k.n_positive / NULLIF(k.n_total, 0)           AS cw_pct_positive,
               100.0 * a.sum_prop_positive / NULLIF(a.n_accounts, 0) AS aw_pct_positive,
               100.0 * k.n_negative / NULLIF(k.n_total, 0)           AS cw_pct_negative,
               100.0 * a.sum_prop_negative / NULLIF(a.n_accounts, 0) AS aw_pct_negative,
               100.0 * k.n_neutral / NULLIF(k.n_total, 0)            AS cw_pct_neutral,
               100.0 * a.sum_prop_neutral / NULLIF(a.n_accounts, 0)  AS aw_pct_neutral,
               a.n_accounts AS n_accounts_aw
        FROM agg_karma_sentiment k
        JOIN agg_account_weighted_sentiment a ON k.category_order = a.category_order
        ORDER BY k.category_order
        """,
    )


def account_age(db: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    return fetch_all(
        db,
        f"""
        SELECT age_category, category_order, n_total, n_positive, n_negative, n_neutral,
               {PCT}, n_accounts
        FROM agg_account_age_sentiment
        ORDER BY category_order
        """,
    )


def verification(db: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    return fetch_all(
        db,
        f"""
        SELECT verified_status, n_total, n_positive, n_negative, n_neutral,
               {PCT}, n_accounts
        FROM agg_verification_sentiment
        ORDER BY n_total DESC
        """,
    )
