from __future__ import annotations
from typing import Any
from ..dialect import Dialect
from ..field import FieldMeta
from ..utils import (
    python_type_to_sql_type,
    column_constraints_sql,
    is_association_field,
)


class MySQLDialect(Dialect):
    """MySQL-specific dialect implementation.

    Requires: pymysql (pip install pymysql)
    """

    def placeholder(self, n: int) -> str:
        return "%s"

    def quote_identifier(self, name: str) -> str:
        return f"`{name}`"

    def data_type_of(self, field_meta: FieldMeta) -> str:
        py_type = field_meta.python_type
        if py_type is int:
            if field_meta.auto_increment:
                return "INT AUTO_INCREMENT"
            return "INT"
        elif py_type is str:
            if field_meta.size > 0:
                return f"VARCHAR({field_meta.size})"
            return "TEXT"
        elif py_type is float:
            return "DOUBLE"
        elif py_type is bool:
            return "TINYINT(1)"
        elif py_type is bytes:
            return "BLOB"
        else:
            return "TEXT"

    def escape_string(self, s: str) -> str:
        return s.replace("\\", "\\\\").replace("'", "\\'")

    def cast_to_db_value(self, value: Any) -> Any:
        if isinstance(value, bool):
            return 1 if value else 0
        return value

    def cast_from_db_value(self, value: Any, python_type: type) -> Any:
        if python_type is bool:
            return bool(value)
        return value

    def create_table_sql(self, model: type) -> str:
        columns_parts: list[str] = []
        pk_columns: list[str] = []

        for field_meta in model.__gorm_fields__.values():
            if is_association_field(field_meta):
                continue
            col_name = self.quote_identifier(field_meta.column_name)
            col_type = self.data_type_of(field_meta)
            constraints = column_constraints_sql(field_meta)
            if field_meta.primary_key and field_meta.auto_increment:
                constraints = constraints.replace("AUTOINCREMENT", "")
            columns_parts.append(f"  {col_name} {col_type}{constraints}")
            if field_meta.primary_key:
                pk_columns.append(col_name)

        if pk_columns:
            columns_parts.append(f"  PRIMARY KEY ({', '.join(pk_columns)})")

        table_name = self.quote_identifier(model.__tablename__)
        return (
            f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
            + ",\n".join(columns_parts)
            + "\n)"
        )

    def add_column_sql(self, table_name: str, field_meta: FieldMeta) -> str:
        col_name = self.quote_identifier(field_meta.column_name)
        col_type = self.data_type_of(field_meta)
        constraints = column_constraints_sql(field_meta)
        tbl = self.quote_identifier(table_name)
        return f"ALTER TABLE {tbl} ADD COLUMN {col_name} {col_type}{constraints}"
