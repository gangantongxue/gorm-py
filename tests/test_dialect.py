import pytest
from gorm.dialect import Dialect
from gorm.dialects.sqlite import SQLiteDialect
from gorm.field import FieldMeta


class TestSQLiteDialect:
    @pytest.fixture
    def dialect(self):
        return SQLiteDialect()

    def test_placeholder(self, dialect):
        assert dialect.placeholder(0) == "?"
        assert dialect.placeholder(1) == "?"
        assert dialect.placeholder(2) == "?"
        assert dialect.placeholder(5) == "?"

    def test_quote_identifier(self, dialect):
        assert dialect.quote_identifier("name") == '"name"'
        assert dialect.quote_identifier("users") == '"users"'

    def test_data_type_int(self, dialect):
        meta = FieldMeta(column_name="id", python_type=int, primary_key=True, auto_increment=True)
        assert "INTEGER" in dialect.data_type_of(meta).upper()

    def test_data_type_str(self, dialect):
        meta = FieldMeta(column_name="name", python_type=str, size=255)
        assert "VARCHAR" in dialect.data_type_of(meta).upper()
        assert "255" in dialect.data_type_of(meta)

    def test_data_type_float(self, dialect):
        meta = FieldMeta(column_name="price", python_type=float)
        assert "REAL" in dialect.data_type_of(meta).upper()

    def test_data_type_bool(self, dialect):
        meta = FieldMeta(column_name="active", python_type=bool)
        result = dialect.data_type_of(meta).upper()
        assert "INTEGER" in result or "BOOLEAN" in result

    def test_data_type_text_no_size(self, dialect):
        meta = FieldMeta(column_name="bio", python_type=str)
        assert "TEXT" in dialect.data_type_of(meta).upper()

    def test_escape_string(self, dialect):
        assert dialect.escape_string("it's ok") == "it''s ok"
        assert dialect.escape_string("hello") == "hello"

    def test_cast_to_db_value(self, dialect):
        assert dialect.cast_to_db_value(True) == 1
        assert dialect.cast_to_db_value(False) == 0
        assert dialect.cast_to_db_value(42) == 42
        assert dialect.cast_to_db_value("hello") == "hello"
        assert dialect.cast_to_db_value(3.14) == 3.14

    def test_cast_from_db_value(self, dialect):
        assert dialect.cast_from_db_value(1, bool) is True
        assert dialect.cast_from_db_value(0, bool) is False
        assert dialect.cast_from_db_value(42, int) == 42
        assert dialect.cast_from_db_value("hello", str) == "hello"


class TestDialectABC:
    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            Dialect()

    def test_concrete_subclass_ok(self):
        class MyDialect(Dialect):
            def placeholder(self, n): return "?"
            def quote_identifier(self, name): return name
            def data_type_of(self, meta): return "TEXT"
            def create_table_sql(self, model): return "CREATE"
            def add_column_sql(self, table, meta): return "ALTER"
            def escape_string(self, s): return s
            def cast_to_db_value(self, v): return v
            def cast_from_db_value(self, v, t): return v

        d = MyDialect()
        assert isinstance(d, Dialect)
        assert d.placeholder(0) == "?"
