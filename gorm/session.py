from __future__ import annotations
import time
from typing import Any, TypeVar

T = TypeVar("T")


class Session:
    """Executes queries against a database connection and maps results to model instances."""

    def __init__(self, conn, dialect, logger=None) -> None:
        self._conn = conn
        self._dialect = dialect
        self._logger = logger

    def _log(self, sql: str, params: list[Any] | None, start: float, rows: int) -> None:
        if self._logger is not None:
            self._logger.trace(sql, params, start, rows)

    def execute(self, sql: str, params: list[Any] | None = None) -> Any:
        """Execute a raw SQL statement and return the cursor."""
        start = time.time()
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params or [])
            return cursor
        except Exception:
            cursor.close()
            raise

    def query_rows(self, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        """Execute SELECT and return list of dicts."""
        start = time.time()
        cursor = self.execute(sql, params)
        try:
            rows = cursor.fetchall()
            if not rows:
                self._log(sql, params, start, 0)
                return []
            if hasattr(rows[0], "keys"):
                keys = rows[0].keys()
                result = [dict(zip(keys, row)) for row in rows]
            else:
                result = []
            self._log(sql, params, start, len(result))
            return result
        finally:
            cursor.close()

    def insert(self, sql: str, params: list[Any] | None = None) -> int:
        """Execute INSERT and return lastrowid."""
        start = time.time()
        cursor = self.execute(sql, params)
        try:
            row_id = cursor.lastrowid or 0
            self._log(sql, params, start, 1)
            return row_id
        finally:
            cursor.close()

    def execute_write(self, sql: str, params: list[Any] | None = None) -> int:
        """Execute INSERT/UPDATE/DELETE and return rowcount."""
        start = time.time()
        cursor = self.execute(sql, params)
        try:
            rowcount = cursor.rowcount
            self._log(sql, params, start, rowcount)
            return rowcount
        finally:
            cursor.close()

    @property
    def connection(self):
        return self._conn

    def map_to_instance(self, row: dict[str, Any], model_cls: type) -> Any:
        """Map a database row dict to a model instance.

        Uses the dialect to cast values from DB representation to Python types.
        """
        kwargs: dict[str, Any] = {}
        for field_name, field_meta in model_cls.__gorm_fields__.items():
            col_name = field_meta.column_name
            if col_name in row:
                raw_value = row[col_name]
                kwargs[field_name] = self._dialect.cast_from_db_value(
                    raw_value, field_meta.python_type
                )
        instance = model_cls(**kwargs)
        return instance
