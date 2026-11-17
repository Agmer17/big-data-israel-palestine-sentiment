from enum import StrEnum
from typing import Any

import duckdb

from app.repositories.base import PCT, fetch_all


class ContingencyVariable(StrEnum):
    karma = "karma"
    comment_score = "comment_score"
    account_age = "account_age"


# Sumber tabel kontingensi (sama dengan yang ditampilkan notebook; kategori 'Unknown' dikeluarkan).
_SOURCES = {
    ContingencyVariable.karma: """
        SELECT karma_category AS category, category_order, n_positive, n_negative, n_neutral
        FROM agg_karma_sentiment WHERE karma_category <> 'Unknown'""",
    ContingencyVariable.comment_score: """
        SELECT score_category AS category, category_order,
               COALESCE(SUM(n_comments) FILTER (WHERE sentiment = 'positive'), 0) AS n_positive,
               COALESCE(SUM(n_comments) FILTER (WHERE sentiment = 'negative'), 0) AS n_negative,
               COALESCE(SUM(n_comments) FILTER (WHERE sentiment = 'neutral'), 0)  AS n_neutral
        FROM agg_comment_score_sentiment WHERE score_category <> 'Unknown'
        GROUP BY score_category, category_order""",
    ContingencyVariable.account_age: """
        SELECT age_category AS category, category_order, n_positive, n_negative, n_neutral
        FROM agg_account_age_sentiment WHERE age_category <> 'Unknown'""",
}


def associations(db: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    return fetch_all(
        db,
        """
        SELECT analysis, n_rows_compared, n_comments, chi2, dof, p_value, cramers_v,
               CASE WHEN cramers_v IS NULL OR isnan(cramers_v) THEN NULL
                    WHEN cramers_v < 0.1 THEN 'negligible'
                    WHEN cramers_v < 0.2 THEN 'lemah'
                    WHEN cramers_v < 0.4 THEN 'sedang'
                    ELSE 'kuat' END AS effect_size
        FROM agg_association_stats
        ORDER BY cramers_v DESC
        """,
    )


def contingency(db: duckdb.DuckDBPyConnection, variable: ContingencyVariable) -> list[dict[str, Any]]:
    return fetch_all(
        db,
        f"""
        WITH c AS ({_SOURCES[variable]}),
        t AS (SELECT *, n_positive + n_negative + n_neutral AS n_total FROM c)
        SELECT category, category_order, n_positive, n_negative, n_neutral, n_total, {PCT}
        FROM t WHERE n_total > 0
        ORDER BY category_order
        """,
    )
