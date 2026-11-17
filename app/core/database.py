import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

import duckdb
from fastapi import Depends, Request

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._con: duckdb.DuckDBPyConnection | None = None

    def open(self) -> None:
        if not self.path.is_file():
            raise FileNotFoundError(
                f"File DuckDB tidak ditemukan: '{self.path}'. "
                "itu file env nya diubah dulu mas jad path workdir :)"
            )
        self._con = duckdb.connect(str(self.path))
        logger.info("[LOG DEBUG] DuckDB terhubung : %s", self.path)

    def close(self) -> None:
        if self._con is not None:
            self._con.close()
            self._con = None

    def cursor(self) -> duckdb.DuckDBPyConnection:
        if self._con is None:
            raise RuntimeError("Database belum dibuka.")
        return self._con.cursor()

    def existing_tables(self) -> set[str]:
        cur = self.cursor()
        try:
            rows = cur.execute("SELECT table_name FROM information_schema.tables").fetchall()
        finally:
            cur.close()
        return {r[0] for r in rows}


def get_db(request: Request) -> Iterator[duckdb.DuckDBPyConnection]:
    cur = request.app.state.db.cursor()
    try:
        yield cur
    finally:
        cur.close()


DB = Annotated[duckdb.DuckDBPyConnection, Depends(get_db)]
