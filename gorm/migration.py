from __future__ import annotations
from typing import Any
from .utils import is_association_field
from .model import resolve_model


class Migrator:
    """Handles auto-migration: creating tables, adding missing columns, creating indexes.

    Follows GORM semantics:
    - Creates table if not exists
    - Adds missing columns (ALTER TABLE ADD COLUMN)
    - Does NOT drop columns or change column types
    """

    def __init__(self, session, dialect) -> None:
        self._session = session
        self._dialect = dialect

    def auto_migrate(self, *models: type) -> None:
        """Auto-migrate the given model classes."""
        for model in models:
            self._migrate_model(model)

    def _migrate_model(self, model: type) -> None:
        """Migrate a single model: create table if needed, add missing columns."""
        table_name = model.__tablename__

        if not self._table_exists(table_name):
            self._create_table(model)
        else:
            self._add_missing_columns(model)

        self._create_indexes(model)
        self._create_junction_tables(model)

    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        rows = self._session.query_rows(sql, [table_name])
        return len(rows) > 0

    def _get_existing_columns(self, table_name: str) -> set[str]:
        """Get set of existing column names for a table."""
        rows = self._session.query_rows(f"PRAGMA table_info({self._dialect.quote_identifier(table_name)})")
        return {row["name"] for row in rows}

    def _create_table(self, model: type) -> None:
        """Create table with all columns and primary key."""
        sql = self._dialect.create_table_sql(model)
        self._session.execute_write(sql)

    def _add_missing_columns(self, model: type) -> None:
        """Add columns that exist in model but not in database."""
        existing = self._get_existing_columns(model.__tablename__)

        for field_meta in model.__gorm_fields__.values():
            if is_association_field(field_meta):
                continue
            if field_meta.column_name not in existing:
                sql = self._dialect.add_column_sql(model.__tablename__, field_meta)
                self._session.execute_write(sql)

    def _create_indexes(self, model: type) -> None:
        """Create indexes for fields marked with index=True or unique=True."""
        table_name = model.__tablename__

        for field_meta in model.__gorm_fields__.values():
            if is_association_field(field_meta):
                continue
            col = self._dialect.quote_identifier(field_meta.column_name)
            tbl = self._dialect.quote_identifier(table_name)

            if field_meta.unique:
                idx_name = f"uni_{table_name}_{field_meta.column_name}"
                sql = f"CREATE UNIQUE INDEX IF NOT EXISTS {self._dialect.quote_identifier(idx_name)} ON {tbl} ({col})"
                self._session.execute_write(sql)
            elif field_meta.index:
                idx_name = f"idx_{table_name}_{field_meta.column_name}"
                sql = f"CREATE INDEX IF NOT EXISTS {self._dialect.quote_identifier(idx_name)} ON {tbl} ({col})"
                self._session.execute_write(sql)

    def create_table(self, model: type) -> None:
        """Create table for a model (without checking existence)."""
        self._create_table(model)

    def drop_table(self, model: type) -> None:
        """Drop table for a model."""
        tbl = self._dialect.quote_identifier(model.__tablename__)
        sql = f"DROP TABLE IF EXISTS {tbl}"
        self._session.execute_write(sql)

    def has_table(self, model: type) -> bool:
        """Check if the model's table exists."""
        return self._table_exists(model.__tablename__)

    def _create_junction_tables(self, model: type) -> None:
        """Create junction tables for many_to_many relationships."""
        for field_meta in model.__gorm_fields__.values():
            if not field_meta.many_to_many:
                continue
            target_cls = resolve_model(field_meta.many_to_many)
            if target_cls is None:
                continue

            from .association import _resolve_junction
            jt, owner_fk, target_fk = _resolve_junction(model, target_cls, field_meta)

            if self._table_exists(jt):
                continue

            q_owner = self._dialect.quote_identifier(owner_fk)
            q_target = self._dialect.quote_identifier(target_fk)
            q_jt = self._dialect.quote_identifier(jt)
            sql = (
                f"CREATE TABLE IF NOT EXISTS {q_jt} (\n"
                f"  {q_owner} INTEGER NOT NULL,\n"
                f"  {q_target} INTEGER NOT NULL,\n"
                f"  PRIMARY KEY ({q_owner}, {q_target})\n"
                f")"
            )
            self._session.execute_write(sql)
