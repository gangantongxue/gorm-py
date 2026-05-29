from __future__ import annotations
import pytest
import sqlite3
from gorm.db import DB
from gorm.model import Model
from gorm.field import Field
from gorm.dialects.sqlite import SQLiteDialect
from gorm.session import Session


class TestNestedTransaction:
    @pytest.fixture
    def user_model(self):
        class User(Model):
            __tablename__ = "users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)

        return User

    @pytest.fixture
    def db(self, user_model):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        dialect = SQLiteDialect()
        session = Session(conn, dialect)
        create_sql = dialect.create_table_sql(user_model)
        conn.execute(create_sql)
        conn.commit()
        return DB(dialect=dialect, session=session, config=None)

    def test_nested_transaction_commit(self, db, user_model):
        def outer(tx):
            tx.create(user_model(name="outer_user"))

            def inner(tx2):
                tx2.create(user_model(name="inner_user"))

            tx.transaction(inner)

        db.transaction(outer)

        users = db.model(user_model).order("id ASC").find()
        assert len(users) == 2
        assert users[0].name == "outer_user"
        assert users[1].name == "inner_user"

    def test_inner_rollback_preserves_outer(self, db, user_model):
        def outer(tx):
            tx.create(user_model(name="outer_user"))

            def inner(tx2):
                tx2.create(user_model(name="inner_user"))
                raise ValueError("inner failure")

            try:
                tx.transaction(inner)
            except ValueError:
                pass

            tx.create(user_model(name="after_inner"))

        db.transaction(outer)

        users = db.model(user_model).order("id ASC").find()
        assert len(users) == 2
        names = {u.name for u in users}
        assert names == {"outer_user", "after_inner"}
