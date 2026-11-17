from typing import Any

import duckdb

from app.repositories.base import fetch_all


def table_row_counts(db: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    """Jumlah baris tiap tabel (padanan verifikasi di akhir notebook)."""
    names = [r["table_name"] for r in fetch_all(db, "SELECT table_name FROM information_schema.tables ORDER BY 1")]
    out = []
    for name in names:
        quoted = '"' + name.replace('"', '""') + '"'  # nama berasal dari catalog DuckDB sendiri
        n = db.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0]
        out.append({"table_name": name, "n_rows": n})
    return out
