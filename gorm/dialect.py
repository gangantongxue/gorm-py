from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class Dialect(ABC):
    """Abstract base for database-specific SQL generation."""

    @abstractmethod
    def placeholder(self, n: int) -> str:
        """Return the parameter placeholder string."""
        ...

    @abstractmethod
    def quote_identifier(self, name: str) -> str:
        """Quote a table or column name."""
        ...

    @abstractmethod
    def data_type_of(self, field_meta) -> str:
        """Return the SQL data type for a field."""
        ...

    @abstractmethod
    def create_table_sql(self, model: type) -> str:
        """Return CREATE TABLE SQL for a model class."""
        ...

    @abstractmethod
    def add_column_sql(self, table_name: str, field_meta) -> str:
        """Return ALTER TABLE ADD COLUMN SQL."""
        ...

    @abstractmethod
    def escape_string(self, s: str) -> str:
        """Escape a string for safe SQL embedding."""
        ...

    @abstractmethod
    def cast_to_db_value(self, value: Any) -> Any:
        """Cast a Python value to its database representation."""
        ...

    @abstractmethod
    def cast_from_db_value(self, value: Any, python_type: type) -> Any:
        """Cast a database value to its Python representation."""
        ...
