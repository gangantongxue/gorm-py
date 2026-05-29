from __future__ import annotations
from dataclasses import dataclass, field as dc_field
from datetime import datetime
from typing import Any, Callable

from .query import Query
from .session import Session
from .model import Model
from .field import FieldMeta, Expression
from .errors import RecordNotFound
from .migration import Migrator
from .utils import is_association_field


@dataclass
class Config:
    auto_migrate: bool = False
    skip_default_transaction: bool = False
    naming_strategy: Any = None
    now_func: Callable[[], datetime] = dc_field(default=datetime.utcnow)
    dry_run: bool = False
    prepare_stmt: bool = True
    log_level: int | None = None
    logger: Any = None


class DB:
    def __init__(
        self,
        dialect=None,
        session=None,
        config=None,
        query=None,
    ) -> None:
        self._dialect = dialect
        self._session = session
        self._config = config or Config()
        self._query = query or Query()
        self._error = None
        self._model_cls = None
        self._model_instance: Model | None = None
        self._preloads: list[tuple[str, tuple]] = []
        self._tx_depth: int = 0

    def _clone(self, **overrides) -> DB:
        new_db = DB.__new__(DB)
        new_db._dialect = overrides.get("_dialect", self._dialect)
        new_db._session = overrides.get("_session", self._session)
        new_db._config = overrides.get("_config", self._config)
        new_db._query = overrides.get("_query", self._query.clone())
        new_db._error = overrides.get("_error", self._error)
        new_db._model_cls = overrides.get("_model_cls", self._model_cls)
        new_db._model_instance = overrides.get("_model_instance", self._model_instance)
        new_db._preloads = overrides.get("_preloads", list(self._preloads))
        new_db._tx_depth = overrides.get("_tx_depth", self._tx_depth)
        return new_db

    def _ensure_model(self, model_cls) -> type:
        if model_cls is not None:
            self._query.table = model_cls.__tablename__
            return model_cls
        raise ValueError("model_cls is required")

    def _apply_soft_delete_filter(self, model_cls: type) -> DB:
        """Clone with soft-delete WHERE condition if the model has one and not unscoped."""
        if self._query.unscoped:
            return self
        sd = model_cls.soft_delete_field()
        if sd is None:
            return self
        q = self._query.clone()
        q.add_where(f"{sd.column_name} IS NULL", [])
        return self._clone(_query=q)

    # ---- Chain methods (return new DB copy) ----

    def model(self, value: type | Model) -> DB:
        """Set the model (class or instance) for subsequent operations."""
        if isinstance(value, type):
            model_cls = value
            instance = None
        else:
            model_cls = type(value)
            instance = value
        q = self._query.clone()
        q.table = model_cls.__tablename__
        return self._clone(_query=q, _model_cls=model_cls, _model_instance=instance)

    def table(self, name: str) -> DB:
        q = self._query.clone()
        q.table = name
        return self._clone(_query=q)

    def where(self, cond: str | Expression, *args: Any) -> DB:
        q = self._query.clone()
        if isinstance(cond, Expression):
            sql, params = cond.compile(self._dialect)
            q.add_where(sql, params)
        else:
            q.add_where(cond, list(args))
        return self._clone(_query=q)

    def or_where(self, cond: str | Expression, *args: Any) -> DB:
        q = self._query.clone()
        if isinstance(cond, Expression):
            sql, params = cond.compile(self._dialect)
            q.add_or_where(sql, params)
        else:
            q.add_or_where(cond, list(args))
        return self._clone(_query=q)

    def not_(self, cond: str | Expression, *args: Any) -> DB:
        q = self._query.clone()
        if isinstance(cond, Expression):
            sql, params = cond.compile(self._dialect)
            q.add_not(sql, params)
        else:
            q.add_not(cond, list(args))
        return self._clone(_query=q)

    def order(self, order_sql: str) -> DB:
        q = self._query.clone()
        q.add_order(order_sql)
        return self._clone(_query=q)

    def limit(self, n: int) -> DB:
        q = self._query.clone()
        q.set_limit(n)
        return self._clone(_query=q)

    def offset(self, n: int) -> DB:
        q = self._query.clone()
        q.set_offset(n)
        return self._clone(_query=q)

    def select(self, *fields: str) -> DB:
        q = self._query.clone()
        q.set_select(list(fields))
        return self._clone(_query=q)

    def unscoped(self) -> DB:
        q = self._query.clone()
        q.unscoped = True
        return self._clone(_query=q)

    def group(self, col: str) -> DB:
        """Add GROUP BY clause."""
        q = self._query.clone()
        q.groups.append(col)
        return self._clone(_query=q)

    def having(self, cond: str, *args: Any) -> DB:
        """Add HAVING clause."""
        q = self._query.clone()
        q.havings.append((cond, list(args)))
        return self._clone(_query=q)

    def join(self, table_name: str, on: str) -> DB:
        """Add INNER JOIN."""
        q = self._query.clone()
        q.joins.append((table_name, on))
        return self._clone(_query=q)

    def distinct(self) -> DB:
        """Add DISTINCT."""
        q = self._query.clone()
        q.distinct = True
        return self._clone(_query=q)

    def raw(self, sql: str, *args: Any) -> list[dict]:
        """Execute raw SQL and return rows as dicts."""
        return self._session.query_rows(sql, list(args))

    def scopes(self, *funcs: Callable) -> DB:
        """Apply scope functions to the query. Each func receives DB and returns DB."""
        db = self
        for fn in funcs:
            db = fn(db)
        return db

    def preload(self, relation: str, *conditions: Any) -> DB:
        """Eager-load a relation."""
        db = self._clone()
        db._preloads.append((relation, conditions))
        return db

    def association(self, field_name: str):
        """Get an Association helper for relationship operations.

        Usage:
            db.model(user).association("orders").find()
        """
        from .association import Association
        if self._model_instance is None:
            raise ValueError("model(instance) must be called before association()")
        return Association(self, self._model_instance, field_name)

    def association_for(self, instance: Model, field_name: str):
        """Get an Association helper for a specific instance.

        Usage:
            db.association_for(user, "orders").find()
        """
        from .association import Association
        return Association(self, instance, field_name)

    # ---- Terminal methods ----

    def create(self, instance: Model) -> Model:
        from .hooks import call_hook, HOOK_BEFORE_SAVE, HOOK_BEFORE_CREATE, HOOK_AFTER_CREATE, HOOK_AFTER_SAVE
        call_hook(instance, HOOK_BEFORE_SAVE)
        call_hook(instance, HOOK_BEFORE_CREATE)

        model_cls = type(instance)
        self._query.table = model_cls.__tablename__

        fields: list[str] = []
        values: list[Any] = []

        for field_name, field_meta in model_cls.__gorm_fields__.items():
            if field_meta.auto_increment and field_meta.primary_key:
                continue  # skip auto-increment PK on insert
            if is_association_field(field_meta):
                continue  # skip association fields
            val = getattr(instance, field_name, None)
            if val is None and (field_meta.auto_now_add or field_meta.auto_now):
                val = self._config.now_func()
                setattr(instance, field_name, val)
            fields.append(field_meta.column_name)
            values.append(self._dialect.cast_to_db_value(val))

        sql, params = self._query.compile_insert(fields, values, self._dialect)
        row_id = self._session.insert(sql, params)

        pk_field = model_cls.primary_key_field()
        if pk_field and pk_field.auto_increment:
            setattr(instance, pk_field.column_name, row_id)

        call_hook(instance, HOOK_AFTER_CREATE)
        call_hook(instance, HOOK_AFTER_SAVE)

        return instance

    def _resolve_model(self, model_cls: type = None) -> type:
        if model_cls is not None:
            self._query.table = model_cls.__tablename__
            return model_cls
        if self._model_cls is not None:
            return self._model_cls
        raise ValueError("model_cls is required")

    def find(self, model_cls: type = None) -> list[Model]:
        from .hooks import call_find_hooks

        model_cls = self._resolve_model(model_cls)
        db = self._apply_soft_delete_filter(model_cls)

        sql, params = db._query.compile_select(self._dialect)
        rows = self._session.query_rows(sql, params)

        results: list[Model] = []
        for row in rows:
            instance = self._session.map_to_instance(row, model_cls)
            results.append(instance)

        # Execute preloads
        if self._preloads and results:
            from .association import preload_relation
            for relation, conditions in self._preloads:
                preload_relation(self, results, relation, model_cls)

        call_find_hooks(results)
        return results

    def first(self, model_cls: type = None) -> Model | None:
        model_cls = self._resolve_model(model_cls)

        q = self._query.clone()
        q.set_limit(1)
        db = self._clone(_query=q, _model_cls=model_cls)
        results = db.find()
        return results[0] if results else None

    def take(self, model_cls: type = None) -> Model | None:
        return self.first(model_cls)

    def last(self, model_cls: type = None) -> Model | None:
        model_cls = self._resolve_model(model_cls)

        pk = model_cls.primary_key_field()
        if pk:
            q = self._query.clone()
            q.add_order(f"{pk.column_name} DESC")
            q.set_limit(1)
            db = self._clone(_query=q, _model_cls=model_cls)
            results = db.find()
            return results[0] if results else None
        return None

    def count(self, model_cls: type = None) -> int:
        model_cls = self._resolve_model(model_cls)
        db = self._apply_soft_delete_filter(model_cls)

        q = db._query.clone()
        q.set_count_mode(True)
        sql, params = q.compile_select(self._dialect)
        rows = self._session.query_rows(sql, params)
        if rows:
            return list(rows[0].values())[0]
        return 0

    def update(self, **columns: Any) -> int:
        updates = {}

        for col_name, value in columns.items():
            updates[col_name] = self._dialect.cast_to_db_value(value)

        sql, params = self._query.compile_update(updates, self._dialect)
        return self._session.execute_write(sql, params)

    def update_column(self, col: str, value: Any) -> int:
        return self.update(**{col: value})

    def delete(self, instance: Model = None) -> int:
        if instance is not None:
            from .hooks import call_hook, HOOK_BEFORE_DELETE, HOOK_AFTER_DELETE
            call_hook(instance, HOOK_BEFORE_DELETE)

            model_cls = type(instance)
            pk = model_cls.primary_key_field()
            if pk is None:
                raise ValueError(f"{model_cls.__name__} has no primary key field")

            pk_value = getattr(instance, pk.column_name)
            q = self._query.clone()
            q.table = model_cls.__tablename__
            q.add_where(f"{pk.column_name} = ?", [pk_value])
            db = self._clone(_query=q, _model_cls=model_cls)
            result = db.delete()
            call_hook(instance, HOOK_AFTER_DELETE)
            return result

        # Check for soft delete
        sd_field = None
        if self._model_cls is not None:
            sd_field = self._model_cls.soft_delete_field()

        if sd_field is not None:
            now = self._config.now_func()
            col = sd_field.column_name
            sql, params = self._query.compile_update(
                {col: now}, self._dialect
            )
            return self._session.execute_write(sql, params)

        sql, params = self._query.compile_delete(self._dialect)
        return self._session.execute_write(sql, params)

    def save(self, instance: Model) -> Model:
        model_cls = type(instance)
        pk = model_cls.primary_key_field()
        if pk is None:
            return self.create(instance)

        pk_value = getattr(instance, pk.column_name, None)
        if pk_value is None:
            return self.create(instance)

        q = self._query.clone()
        q.table = model_cls.__tablename__
        q.add_where(f"{pk.column_name} = ?", [pk_value])
        db = self._clone(_query=q)

        existing = db.first(model_cls)
        if existing is not None:
            from .hooks import call_hook, HOOK_BEFORE_SAVE, HOOK_BEFORE_UPDATE, HOOK_AFTER_UPDATE, HOOK_AFTER_SAVE
            call_hook(instance, HOOK_BEFORE_SAVE)
            call_hook(instance, HOOK_BEFORE_UPDATE)

            updates: dict[str, Any] = {}
            for field_name, field_meta in model_cls.__gorm_fields__.items():
                if is_association_field(field_meta):
                    continue
                val = getattr(instance, field_name, None)
                if field_meta.auto_now:
                    val = self._config.now_func()
                    setattr(instance, field_name, val)
                if val is not None:
                    updates[field_meta.column_name] = self._dialect.cast_to_db_value(val)
            db.update(**updates)
            call_hook(instance, HOOK_AFTER_UPDATE)
            call_hook(instance, HOOK_AFTER_SAVE)
            return instance
        else:
            return self.create(instance)

    def exists(self, model_cls: type = None) -> bool:
        if model_cls is not None:
            self._query.table = model_cls.__tablename__
        return self.count(model_cls) > 0

    def begin(self) -> DB:
        """Begin a transaction. Returns a new DB with transaction state."""
        session = self._session
        if self._tx_depth == 0:
            try:
                session.connection.commit()
            except Exception:
                pass
            session.connection.execute("BEGIN")
        else:
            session.connection.execute(f"SAVEPOINT _gorm_sp_{self._tx_depth}")
        return self._clone(_session=session, _tx_depth=self._tx_depth + 1)

    def commit(self) -> DB:
        """Commit the current transaction."""
        self._tx_depth -= 1
        if self._tx_depth > 0:
            self._session.connection.execute(f"RELEASE _gorm_sp_{self._tx_depth}")
        else:
            self._session.connection.execute("COMMIT")
        return self

    def rollback(self) -> DB:
        """Rollback the current transaction."""
        self._tx_depth -= 1
        if self._tx_depth > 0:
            self._session.connection.execute(f"ROLLBACK TO _gorm_sp_{self._tx_depth}")
        else:
            self._session.connection.execute("ROLLBACK")
        return self

    def transaction(self, fn, *args, **kwargs) -> Any:
        """Execute fn(tx) in a transaction. Auto-commit on success, auto-rollback on exception.

        fn receives a transaction DB as the first argument.
        Supports nested transactions via savepoints.
        """
        tx = self.begin()
        try:
            result = fn(tx, *args, **kwargs)
            tx.commit()
            return result
        except Exception:
            tx.rollback()
            raise

    def auto_migrate(self, *models: type) -> None:
        """Auto-migrate the given model classes."""
        migrator = Migrator(self._session, self._dialect)
        migrator.auto_migrate(*models)

    def create_table(self, model: type) -> None:
        """Create table for a model."""
        migrator = Migrator(self._session, self._dialect)
        migrator.create_table(model)

    def drop_table(self, model: type) -> None:
        """Drop table for a model."""
        migrator = Migrator(self._session, self._dialect)
        migrator.drop_table(model)

    def has_table(self, model: type) -> bool:
        """Check if table exists for a model."""
        migrator = Migrator(self._session, self._dialect)
        return migrator.has_table(model)


def open_db(dsn: str, config: Config | None = None) -> DB:
    """Open a database connection from a DSN string.

    Supported formats:
        sqlite:///path/to/db
        sqlite://:memory:
        postgres://user:pass@host:port/dbname
        mysql://user:pass@host:port/dbname
    """
    if config is None:
        config = Config()

    from .session import Session
    from .logger import Logger

    gorm_logger = None
    if config.logger is not None:
        gorm_logger = config.logger
    elif config.log_level is not None:
        gorm_logger = Logger(log_level=config.log_level)

    if dsn.startswith("sqlite://"):
        return _open_sqlite(dsn, config, gorm_logger)
    elif dsn.startswith("postgres://") or dsn.startswith("postgresql://"):
        return _open_postgres(dsn, config, gorm_logger)
    elif dsn.startswith("mysql://"):
        return _open_mysql(dsn, config, gorm_logger)

    raise ValueError(f"Unsupported database DSN: {dsn}")


def _open_sqlite(dsn: str, config: Config, gorm_logger) -> DB:
    import sqlite3

    path = dsn[len("sqlite://"):]
    if path == ":memory:":
        conn = sqlite3.connect(":memory:")
    else:
        conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    from .dialects.sqlite import SQLiteDialect

    dialect = SQLiteDialect()
    session = Session(conn, dialect, logger=gorm_logger)
    return DB(dialect=dialect, session=session, config=config)


def _open_postgres(dsn: str, config: Config, gorm_logger) -> DB:
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        raise ImportError(
            "psycopg2 is required for PostgreSQL support. Install with: pip install psycopg2-binary"
        )

    conn = psycopg2.connect(dsn)
    conn.cursor_factory = psycopg2.extras.RealDictCursor

    from .dialects.postgres import PostgresDialect

    dialect = PostgresDialect()
    session = Session(conn, dialect, logger=gorm_logger)
    return DB(dialect=dialect, session=session, config=config)


def _open_mysql(dsn: str, config: Config, gorm_logger) -> DB:
    try:
        import pymysql
    except ImportError:
        raise ImportError(
            "pymysql is required for MySQL support. Install with: pip install pymysql"
        )

    from urllib.parse import urlparse

    url = urlparse(dsn)
    conn = pymysql.connect(
        host=url.hostname or "localhost",
        port=url.port or 3306,
        user=url.username or "root",
        password=url.password or "",
        database=url.path.lstrip("/"),
        cursorclass=pymysql.cursors.DictCursor,
    )

    from .dialects.mysql import MySQLDialect

    dialect = MySQLDialect()
    session = Session(conn, dialect, logger=gorm_logger)
    return DB(dialect=dialect, session=session, config=config)
