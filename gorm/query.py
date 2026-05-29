from __future__ import annotations
from dataclasses import dataclass, field as dc_field
from typing import Any


@dataclass
class Query:
    """Holds query state and compiles to SQL + parameters.

    Immutable-copy pattern: use clone() to derive a new Query with modifications.
    """

    table: str = ""

    # SELECT options
    select_fields: list[str] = dc_field(default_factory=list)
    distinct: bool = False
    count_mode: bool = False

    # Conditions: list of (operator, sql_fragment, params)
    # operator is "AND", "OR", or "NOT"
    conditions: list[tuple[str, str, list[Any]]] = dc_field(default_factory=list)

    # Order, limit, offset
    orders: list[str] = dc_field(default_factory=list)
    limit_val: int | None = None
    offset_val: int | None = None

    # GROUP BY / HAVING
    groups: list[str] = dc_field(default_factory=list)
    havings: list[tuple[str, list[Any]]] = dc_field(default_factory=list)

    # JOINs: list of (table, on_condition)
    joins: list[tuple[str, str]] = dc_field(default_factory=list)

    # Soft delete filter
    unscoped: bool = False

    def clone(self) -> Query:
        """Return a deep copy for immutable chain pattern."""
        return Query(
            table=self.table,
            select_fields=list(self.select_fields),
            distinct=self.distinct,
            count_mode=self.count_mode,
            conditions=[(op, frag, list(p)) for op, frag, p in self.conditions],
            orders=list(self.orders),
            limit_val=self.limit_val,
            offset_val=self.offset_val,
            groups=list(self.groups),
            havings=[(frag, list(p)) for frag, p in self.havings],
            joins=[(t, on) for t, on in self.joins],
            unscoped=self.unscoped,
        )

    def add_where(self, sql: str, params: list[Any]) -> None:
        self.conditions.append(("AND", sql, params))

    def add_or_where(self, sql: str, params: list[Any]) -> None:
        self.conditions.append(("OR", sql, params))

    def add_not(self, sql: str, params: list[Any]) -> None:
        self.conditions.append(("NOT", sql, params))

    def add_order(self, order_sql: str) -> None:
        self.orders.append(order_sql)

    def set_limit(self, n: int) -> None:
        self.limit_val = n

    def set_offset(self, n: int) -> None:
        self.offset_val = n

    def set_select(self, fields: list[str]) -> None:
        self.select_fields = fields

    def set_count_mode(self, enabled: bool) -> None:
        self.count_mode = enabled

    def compile_select(self, dialect) -> tuple[str, list[Any]]:
        """Compile to SELECT SQL + params."""
        parts: list[str] = ["SELECT"]

        # SELECT clause
        if self.distinct:
            parts.append("DISTINCT")
        if self.count_mode:
            parts.append("COUNT(*)")
        elif self.select_fields:
            parts.append(", ".join(self.select_fields))
        else:
            parts.append("*")

        parts.append(f"FROM {dialect.quote_identifier(self.table)}")

        # JOINs
        for join_table, on_cond in self.joins:
            quoted = dialect.quote_identifier(join_table)
            parts.append(f"INNER JOIN {quoted} ON {on_cond}")

        # WHERE
        where_clause, where_params = self._compile_where()
        if where_clause:
            parts.append(f"WHERE {where_clause}")

        # GROUP BY
        if self.groups:
            parts.append(f"GROUP BY {', '.join(self.groups)}")

        # HAVING
        if self.havings:
            having_parts: list[str] = []
            having_params: list[Any] = []
            for having_sql, hp in self.havings:
                having_parts.append(having_sql)
                having_params.extend(hp)
            parts.append(f"HAVING {' AND '.join(having_parts)}")
            where_params.extend(having_params)

        # ORDER BY
        if self.orders:
            parts.append(f"ORDER BY {', '.join(self.orders)}")

        # LIMIT / OFFSET
        if self.limit_val is not None:
            parts.append(f"LIMIT {self.limit_val}")
        if self.offset_val is not None:
            parts.append(f"OFFSET {self.offset_val}")

        sql = " ".join(parts)
        return sql, where_params

    def compile_insert(self, fields: list[str], values: list[Any], dialect) -> tuple[str, list[Any]]:
        """Compile to INSERT SQL + params."""
        quoted_fields = [dialect.quote_identifier(f) for f in fields]
        placeholders = [dialect.placeholder(i) for i in range(len(values))]
        table = dialect.quote_identifier(self.table)
        sql = f'INSERT INTO {table} ({", ".join(quoted_fields)}) VALUES ({", ".join(placeholders)})'
        return sql, list(values)

    def compile_update(self, updates: dict[str, Any], dialect) -> tuple[str, list[Any]]:
        """Compile to UPDATE SQL + params."""
        set_parts: list[str] = []
        params: list[Any] = []
        for col, value in updates.items():
            set_parts.append(f'{dialect.quote_identifier(col)}=?')
            params.append(value)

        where_clause, where_params = self._compile_where()
        params.extend(where_params)

        table = dialect.quote_identifier(self.table)
        sql = f'UPDATE {table} SET {", ".join(set_parts)}'
        if where_clause:
            sql += f" WHERE {where_clause}"
        return sql, params

    def compile_delete(self, dialect) -> tuple[str, list[Any]]:
        """Compile to DELETE SQL + params."""
        where_clause, params = self._compile_where()
        table = dialect.quote_identifier(self.table)
        sql = f"DELETE FROM {table}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        return sql, params

    def _compile_where(self) -> tuple[str, list[Any]]:
        """Compile conditions into WHERE clause fragment and params."""
        if not self.conditions:
            return "", []

        parts: list[str] = []
        params: list[Any] = []

        for i, (op, sql_frag, p) in enumerate(self.conditions):
            if i == 0:
                if op == "NOT":
                    parts.append(f"NOT {sql_frag}")
                else:
                    parts.append(sql_frag)
            else:
                if op == "NOT":
                    parts.append(f"AND NOT {sql_frag}")
                else:
                    parts.append(f"{op} {sql_frag}")
            params.extend(p)

        return " ".join(parts), params
