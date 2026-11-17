from typing import Any

import duckdb

from app.constants import SENTIMENTS, THEMES
from app.repositories.base import fetch_all, paginate


def top_keywords(
    db: duckdb.DuckDBPyConnection, source_field: str, sentiment: str | None, page
) -> tuple[list[dict[str, Any]], int]:
    conds, params = ["source_field = ?"], [source_field]
    if sentiment:
        conds.append("sentiment = ?")
        params.append(sentiment)
    select_sql = f"""
        SELECT keyword, SUM(n_occurrences) AS n_occurrences
        FROM agg_keyword_sentiment
        WHERE {' AND '.join(conds)}
        GROUP BY keyword
    """
    return paginate(db, select_sql, params, "n_occurrences DESC, keyword", page)


def distinctive_keywords(db: duckdb.DuckDBPyConnection, sentiment: str, min_occurrences: int, limit: int) -> list[dict[str, Any]]:
    if sentiment not in SENTIMENTS:  
        raise ValueError(sentiment)
    others = [x for x in SENTIMENTS if x != sentiment]
    n_class, t_class = f"n_{sentiment}", f"t_{sentiment}"
    n_other = " + ".join(f"n_{x}" for x in others)
    t_other = " + ".join(f"t_{x}" for x in others)
    return fetch_all(
        db,
        f"""
        WITH k AS (
            SELECT keyword,
                   SUM(n_occurrences) FILTER (WHERE sentiment = 'positive') AS n_positive,
                   SUM(n_occurrences) FILTER (WHERE sentiment = 'negative') AS n_negative,
                   SUM(n_occurrences) FILTER (WHERE sentiment = 'neutral')  AS n_neutral
            FROM agg_keyword_sentiment WHERE source_field = 'comment' GROUP BY keyword
        ), tot AS (
            SELECT SUM(n_occurrences) FILTER (WHERE sentiment = 'positive') AS t_positive,
                   SUM(n_occurrences) FILTER (WHERE sentiment = 'negative') AS t_negative,
                   SUM(n_occurrences) FILTER (WHERE sentiment = 'neutral')  AS t_neutral
            FROM agg_keyword_sentiment WHERE source_field = 'comment'
        ), vocab AS (
            SELECT COUNT(DISTINCT keyword) AS v
            FROM agg_keyword_sentiment WHERE source_field = 'comment'
        )
        SELECT keyword,
               {n_class} AS n_occurrences,
               10000.0 * {n_class} / NULLIF({t_class}, 0) AS per_10k_tokens,
               log(2, (({n_class} + 0.5) / ({t_class} + 0.5 * v))
                      / (({n_other} + 0.5) / ({t_other} + 0.5 * v))) AS log2_ratio
        FROM k, tot, vocab
        WHERE {n_class} >= ?
        ORDER BY log2_ratio DESC NULLS LAST, keyword
        LIMIT ?
        """,
        [min_occurrences, limit],
    )


def negative_vs_positive(db: duckdb.DuckDBPyConnection, direction: str, min_occurrences: int, limit: int) -> list[dict[str, Any]]:
    order = "DESC" if direction == "negative" else "ASC"
    return fetch_all(
        db,
        f"""
        WITH k AS (
            SELECT keyword,
                   SUM(n_occurrences) FILTER (WHERE sentiment = 'positive') AS n_pos,
                   SUM(n_occurrences) FILTER (WHERE sentiment = 'negative') AS n_neg
            FROM agg_keyword_sentiment WHERE source_field = 'comment' GROUP BY keyword
        ), tot AS (
            SELECT SUM(n_occurrences) FILTER (WHERE sentiment = 'positive') AS t_pos,
                   SUM(n_occurrences) FILTER (WHERE sentiment = 'negative') AS t_neg
            FROM agg_keyword_sentiment WHERE source_field = 'comment'
        ), vocab AS (
            SELECT COUNT(DISTINCT keyword) AS v
            FROM agg_keyword_sentiment WHERE source_field = 'comment'
        )
        SELECT keyword, n_pos AS n_positive, n_neg AS n_negative,
               log(2, ((n_neg + 0.5) / (t_neg + 0.5 * v)) / ((n_pos + 0.5) / (t_pos + 0.5 * v))) AS neg_vs_pos_log2_ratio
        FROM k, tot, vocab
        WHERE n_pos >= ? AND n_neg >= ?
        ORDER BY neg_vs_pos_log2_ratio {order} NULLS LAST, keyword
        LIMIT ?
        """,
        [min_occurrences, min_occurrences, limit],
    )


def _theme_case() -> str:
    whens = []
    for theme, words in THEMES.items():
        in_list = ", ".join("'" + w.replace("'", "''") + "'" for w in words)
        t = theme.replace("'", "''")
        whens.append(f"WHEN keyword IN ({in_list}) THEN '{t}'")
    return "CASE " + " ".join(whens) + " END"


def themes(db: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    return fetch_all(
        db,
        f"""
        WITH t AS (
            SELECT keyword, sentiment, n_occurrences
            FROM agg_keyword_sentiment
            WHERE source_field = 'comment' AND sentiment IN ('positive', 'negative', 'neutral')
        ), m AS (
            SELECT {_theme_case()} AS theme, sentiment, n_occurrences FROM t
        ), tot AS (
            SELECT sentiment, SUM(n_occurrences) AS n_tokens FROM t GROUP BY sentiment
        )
        SELECT m.theme, m.sentiment,
               SUM(m.n_occurrences) AS n_occurrences,
               10000.0 * SUM(m.n_occurrences) / NULLIF(ANY_VALUE(tot.n_tokens), 0) AS per_10k_tokens
        FROM m JOIN tot USING (sentiment)
        WHERE m.theme IS NOT NULL
        GROUP BY m.theme, m.sentiment
        ORDER BY m.theme, m.sentiment
        """,
    )
