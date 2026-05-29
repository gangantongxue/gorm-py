from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class FieldMeta:
    """Metadata describing a database column."""
    column_name: str
    python_type: type
    primary_key: bool = False
    auto_increment: bool = False
    default: Any = None
    unique: bool = False
    index: bool = False
    nullable: bool = False
    size: int = 0
    auto_now: bool = False
    auto_now_add: bool = False
    comment: str = ""
    soft_delete: bool = False
    belongs_to: str | None = None
    has_one: str | None = None
    has_many: str | None = None
    many_to_many: str | None = None
    foreign_key: str | None = None
    join_table: str | None = None
    join_foreign_key: str | None = None
    join_references: str | None = None


class Expression:
    """Represents a column-operator-value expression for lambda-style queries.

    Supports chaining with & (AND) and | (OR).
    """

    def __init__(self, column: str, operator: str, value: Any) -> None:
        self.column = column
        self.operator = operator
        self.value = value
        self._children: list[Expression] = []
        self._joiner: str = ""

    def compile(self, dialect) -> tuple[str, list[Any]]:
        """Compile to SQL fragment and params."""
        placeholder = dialect.placeholder(0)
        col = dialect.quote_identifier(self.column)

        if self._children:
            parts: list[str] = []
            params: list[Any] = []
            for child in self._children:
                child_sql, child_params = child.compile(dialect)
                parts.append(child_sql)
                params.extend(child_params)
            joiner = f" {self._joiner} "
            return joiner.join(parts), params

        if self.operator == "IN":
            placeholders = ", ".join(dialect.placeholder(i) for i in range(len(self.value)))
            return f"{col} IN ({placeholders})", list(self.value)

        if self.operator == "BETWEEN":
            return f"{col} BETWEEN {placeholder} AND {placeholder}", [self.value[0], self.value[1]]

        if self.operator == "LIKE":
            return f"{col} LIKE {placeholder}", [self.value]

        if self.operator == "IS NULL":
            return f"{col} IS NULL", []

        if self.operator == "IS NOT NULL":
            return f"{col} IS NOT NULL", []

        return f"{col} {self.operator} {placeholder}", [self.value]

    def __and__(self, other: Expression) -> Expression:
        result = Expression("", "", None)
        result._children = [self, other]
        result._joiner = "AND"
        return result

    def __or__(self, other: Expression) -> Expression:
        result = Expression("", "", None)
        result._children = [self, other]
        result._joiner = "OR"
        return result

    def __invert__(self) -> Expression:
        result = Expression("", "", None)
        negated = Expression(self.column, "!=" if self.operator == "=" else self.operator, self.value)
        negated._children = list(self._children)
        negated._joiner = self._joiner
        # Wrap with NOT
        child_sql, child_params = negated._compile_simple()
        wrapper = Expression("", "", None)
        wrapper._wrapped_sql = f"NOT ({child_sql})"
        wrapper._wrapped_params = child_params
        return wrapper

    def _compile_simple(self) -> tuple[str, list[Any]]:
        """Compile without quoting (for NOT wrapping)."""
        if self.operator == "IS NULL":
            return f"{self.column} IS NULL", []
        if self.operator == "IS NOT NULL":
            return f"{self.column} IS NOT NULL", []
        return f"{self.column} {self.operator} ?", [self.value]


class Field:
    """Descriptor for model fields. Carries column metadata from GORM-style kwargs.

    Supports lambda-style query expressions via operator overloading:
        db.where(User.age > 18)
        db.where(User.name == "jinzhu")
    """

    def __init__(self, **kwargs: Any) -> None:
        self._kwargs: dict[str, Any] = kwargs
        self._field_name: str = ""

    def _meta(self, *, column_name: str, python_type: type) -> FieldMeta:
        """Build FieldMeta from stored kwargs plus column name and type."""
        kwargs = dict(self._kwargs)
        for key in ("belongs_to", "has_one", "has_many", "many_to_many"):
            val = kwargs.get(key)
            if val is not None and not isinstance(val, str):
                kwargs[key] = val.__name__
        return FieldMeta(
            column_name=column_name,
            python_type=python_type,
            **kwargs,
        )

    def __set_name__(self, owner: type, name: str) -> None:
        self._field_name = name

    def __get__(self, instance: Any, owner: type) -> Any:
        if instance is None:
            return self
        return instance.__dict__.get(self._field_name)

    def __set__(self, instance: Any, value: Any) -> None:
        instance.__dict__[self._field_name] = value

    # ---- Operator overloads for lambda expressions ----

    def __eq__(self, other: Any) -> Expression:  # type: ignore[override]
        if other is None:
            return Expression(self._field_name, "IS NULL", None)
        return Expression(self._field_name, "=", other)

    def __ne__(self, other: Any) -> Expression:  # type: ignore[override]
        if other is None:
            return Expression(self._field_name, "IS NOT NULL", None)
        return Expression(self._field_name, "!=", other)

    def __gt__(self, other: Any) -> Expression:
        return Expression(self._field_name, ">", other)

    def __ge__(self, other: Any) -> Expression:
        return Expression(self._field_name, ">=", other)

    def __lt__(self, other: Any) -> Expression:
        return Expression(self._field_name, "<", other)

    def __le__(self, other: Any) -> Expression:
        return Expression(self._field_name, "<=", other)

    def like(self, pattern: str) -> Expression:
        return Expression(self._field_name, "LIKE", pattern)

    def in_(self, values: list[Any]) -> Expression:
        return Expression(self._field_name, "IN", values)

    def between(self, start: Any, end: Any) -> Expression:
        return Expression(self._field_name, "BETWEEN", (start, end))
