import pytest
import sqlite3
from gorm.migration import Migrator
from gorm.model import Model
from gorm.field import Field
from gorm.dialects.sqlite import SQLiteDialect
from gorm.session import Session


class TestAutoMigrate:
    @pytest.fixture
    def user_model(self):
        class User(Model):
            __tablename__ = "users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255, index=True)
            email: str = Field(size=255, unique=True)

        return User

    @pytest.fixture
    def migrator(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        dialect = SQLiteDialect()
        session = Session(conn, dialect)
        return Migrator(session, dialect)

    def test_auto_migrate_creates_table(self, migrator, user_model):
        assert migrator.has_table(user_model) is False
        migrator.auto_migrate(user_model)
        assert migrator.has_table(user_model) is True

    def test_auto_migrate_is_idempotent(self, migrator, user_model):
        migrator.auto_migrate(user_model)
        migrator.auto_migrate(user_model)
        assert migrator.has_table(user_model) is True

    def test_auto_migrate_adds_missing_column(self, migrator):
        class V1(Model):
            __tablename__ = "users_v1"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)

        migrator.auto_migrate(V1)

        class V2(Model):
            __tablename__ = "users_v1"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)
            age: int = Field(default=18)

        migrator.auto_migrate(V2)

        rows = migrator._session.query_rows(
            f'PRAGMA table_info("{V2.__tablename__}")'
        )
        col_names = {r["name"] for r in rows}
        assert "age" in col_names

    def test_drop_table(self, migrator, user_model):
        migrator.auto_migrate(user_model)
        assert migrator.has_table(user_model) is True
        migrator.drop_table(user_model)
        assert migrator.has_table(user_model) is False

    def test_create_indexes(self, migrator, user_model):
        migrator.auto_migrate(user_model)
        rows = migrator._session.query_rows(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?",
            [user_model.__tablename__],
        )
        index_names = {r["name"] for r in rows}
        assert f"idx_{user_model.__tablename__}_name" in index_names
        assert f"uni_{user_model.__tablename__}_email" in index_names
