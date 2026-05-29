from __future__ import annotations
import pytest
from gorm.dialect import Dialect
from gorm.dialects.postgres import PostgresDialect
from gorm.dialects.mysql import MySQLDialect
from gorm.model import Model
from gorm.field import Field, FieldMeta


class TestPostgresDialect:
    @pytest.fixture
    def dialect(self):
        return PostgresDialect()

    def test_placeholder(self, dialect):
        assert dialect.placeholder(0) == "$1"
        assert dialect.placeholder(1) == "$2"
        assert dialect.placeholder(5) == "$6"

    def test_data_type_bool(self, dialect):
        meta = FieldMeta(column_name="active", python_type=bool)
        assert "BOOLEAN" in dialect.data_type_of(meta).upper()

    def test_data_type_serial(self, dialect):
        meta = FieldMeta(column_name="id", python_type=int, primary_key=True, auto_increment=True)
        assert "SERIAL" in dialect.data_type_of(meta)

    def test_create_table_sql(self, dialect):
        class User(Model):
            __tablename__ = "users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)

        sql = dialect.create_table_sql(User)
        assert "CREATE TABLE IF NOT EXISTS" in sql
        assert '"users"' in sql
        assert "SERIAL PRIMARY KEY" in sql


class TestMySQLDialect:
    @pytest.fixture
    def dialect(self):
        return MySQLDialect()

    def test_placeholder(self, dialect):
        assert dialect.placeholder(0) == "%s"
        assert dialect.placeholder(10) == "%s"

    def test_quote_identifier(self, dialect):
        assert dialect.quote_identifier("name") == "`name`"

    def test_data_type_bool(self, dialect):
        meta = FieldMeta(column_name="active", python_type=bool)
        assert "TINYINT" in dialect.data_type_of(meta).upper()

    def test_data_type_auto_increment(self, dialect):
        meta = FieldMeta(column_name="id", python_type=int, primary_key=True, auto_increment=True)
        assert "AUTO_INCREMENT" in dialect.data_type_of(meta).upper()

    def test_create_table_sql(self, dialect):
        class User(Model):
            __tablename__ = "users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)

        sql = dialect.create_table_sql(User)
        assert "CREATE TABLE IF NOT EXISTS" in sql
        assert "`users`" in sql
        assert "AUTO_INCREMENT" in sql
