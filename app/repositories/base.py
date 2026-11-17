from typing import Any

import duckdb

from app.schemas.common import Page
from app.utils.serialization import sanitize

PCT = """
    100.0 * n_positive / NULLIF(n_total, 0) AS pct_positive,
    100.0 * n_negative / NULLIF(n_total, 0) AS pct_negative,
    100.0 * n_neutral  / NULLIF(n_total, 0) AS pct_neutral
"""


def fetch_all(db: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
    cur = db.execute(sql, params or [])
    cols = [d[0] for d in cur.description]
    return [sanitize(dict(zip(cols, row))) for row in cur.fetchall()]


def fetch_one(db: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> dict[str, Any] | None:
    rows = fetch_all(db, sql, params)
    return rows[0] if rows else None


def paginate(
    db: duckdb.DuckDBPyConnection,
    select_sql: str,
    params: list[Any],
    order_by: str,
    page: Page,
) -> tuple[list[dict[str, Any]], int]:
    total = db.execute(f"SELECT COUNT(*) FROM ({select_sql})", params).fetchone()[0]
    rows = fetch_all(
        db,
        f"SELECT * FROM ({select_sql}) ORDER BY {order_by} LIMIT ? OFFSET ?",
        [*params, page.page_size, page.offset],
    )
    return rows, total


def where_clause(conditions: list[str]) -> str:
    return f"WHERE {' AND '.join(conditions)}" if conditions else ""
