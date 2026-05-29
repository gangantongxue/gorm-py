from __future__ import annotations
from .db import DB, Config, open_db
from .model import Model, GormModel
from .field import Field
from .errors import (
    GormError,
    DBError,
    RecordNotFound,
    InvalidFieldError,
    MigrationError,
)


def open(dsn: str, config: Config | None = None) -> DB:
    """Open a database connection.

    Args:
        dsn: Data source name. e.g. "sqlite:///app.db" or "sqlite://:memory:"
        config: Optional configuration.

    Returns:
        A DB instance ready for queries.
    """
    return open_db(dsn, config)


__all__ = [
    "open",
    "DB",
    "Config",
    "Model",
    "GormModel",
    "Field",
    "GormError",
    "DBError",
    "RecordNotFound",
    "InvalidFieldError",
    "MigrationError",
]
