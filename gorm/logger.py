from __future__ import annotations
import time
import logging
from typing import Any, Callable


class Logger:
    """GORM-style SQL logger.

    Outputs SQL statements with execution time and affected row count.
    """

    def __init__(
        self,
        writer: Callable[[str], None] | None = None,
        log_level: int | None = None,
    ) -> None:
        if writer is not None:
            self._write = writer
        elif log_level is not None:
            logger = logging.getLogger("gorm")
            logger.setLevel(log_level)
            if not logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(logging.Formatter("%(message)s"))
                logger.addHandler(handler)
            self._write = lambda msg: logger.log(log_level, msg)
        else:
            self._write = lambda _: None

    def trace(
        self,
        sql: str,
        params: list[Any] | None,
        start_time: float,
        affected_rows: int,
    ) -> None:
        duration = (time.time() - start_time) * 1000
        msg = f"[{duration:.2f}ms] [rows:{affected_rows}] {sql}"
        self._write(msg)
