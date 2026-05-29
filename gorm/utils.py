from __future__ import annotations
from typing import Any
from .field import FieldMeta


def python_type_to_sql_type(field_meta: FieldMeta) -> str:
    """Map a Python type + FieldMeta options to a SQL column type."""
    py_type = field_meta.python_type

    if py_type is int:
        return "INTEGER"
    elif py_type is str:
        if field_meta.size > 0:
            return f"VARCHAR({field_meta.size})"
        return "TEXT"
    elif py_type is float:
        return "REAL"
    elif py_type is bool:
        return "INTEGER"
    elif py_type is bytes:
        return "BLOB"
    else:
        return "TEXT"


def column_constraints_sql(field_meta: FieldMeta) -> str:
    """Build column constraint clause from FieldMeta.

    Note: UNIQUE is handled by _create_indexes (CREATE UNIQUE INDEX),
    not in the column definition, for consistency between initial creation
    and migration (ALTER TABLE ADD COLUMN does not support UNIQUE in SQLite).
    """
    parts: list[str] = []
    if field_meta.primary_key:
        pass  # handled separately in create_table_sql for PKs
    if field_meta.nullable:
        parts.append("NULL")
    else:
        parts.append("NOT NULL")
    if field_meta.default is not None and not field_meta.auto_increment:
        default_val = field_meta.default
        if isinstance(default_val, str):
            parts.append(f"DEFAULT '{default_val}'")
        else:
            parts.append(f"DEFAULT {default_val}")
    if field_meta.auto_increment and not field_meta.primary_key:
        parts.append("AUTOINCREMENT")
    return " " + " ".join(parts) if parts else ""


def snake_to_camel(name: str) -> str:
    """Convert snake_case to CamelCase."""
    return "".join(word.capitalize() for word in name.split("_"))


def is_association_field(field_meta: FieldMeta) -> bool:
    """Check if a FieldMeta represents an association (not a real column)."""
    return bool(
        field_meta.belongs_to
        or field_meta.has_one
        or field_meta.has_many
        or field_meta.many_to_many
    )
