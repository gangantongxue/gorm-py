import pytest
import sqlite3
from gorm.db import DB
from gorm.model import Model
from gorm.field import Field
from gorm.dialects.sqlite import SQLiteDialect
from gorm.session import Session


class TestHooks:
    @pytest.fixture
    def hook_model(self):
        """Model that tracks hook calls."""
        class HookUser(Model):
            __tablename__ = "hook_users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)

            calls: list[str] = []

            def before_save(self):
                HookUser.calls.append("before_save")

            def after_save(self):
                HookUser.calls.append("after_save")

            def before_create(self):
                HookUser.calls.append("before_create")

            def after_create(self):
                HookUser.calls.append("after_create")

            def before_update(self):
                HookUser.calls.append("before_update")

            def after_update(self):
                HookUser.calls.append("after_update")

            def before_delete(self):
                HookUser.calls.append("before_delete")

            def after_delete(self):
                HookUser.calls.append("after_delete")

            def after_find(self):
                HookUser.calls.append("after_find")

        return HookUser

    @pytest.fixture
    def db(self, hook_model):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        dialect = SQLiteDialect()
        session = Session(conn, dialect)
        create_sql = dialect.create_table_sql(hook_model)
        conn.execute(create_sql)
        conn.commit()
        return DB(dialect=dialect, session=session, config=None)

    def test_create_hooks_order(self, db, hook_model):
        hook_model.calls = []
        u = hook_model(name="test")
        db.create(u)

        expected = ["before_save", "before_create", "after_create", "after_save"]
        assert hook_model.calls == expected

    def test_update_hooks_order(self, db, hook_model):
        hook_model.calls = []
        u = db.create(hook_model(name="test"))
        hook_model.calls = []  # reset

        u.name = "updated"
        db.save(u)

        expected = ["after_find", "before_save", "before_update", "after_update", "after_save"]
        assert hook_model.calls == expected

    def test_delete_hooks_order(self, db, hook_model):
        hook_model.calls = []
        u = db.create(hook_model(name="test"))
        hook_model.calls = []  # reset

        db.delete(u)

        expected = ["before_delete", "after_delete"]
        assert hook_model.calls == expected

    def test_after_find_hook_called(self, db, hook_model):
        hook_model.calls = []
        db.create(hook_model(name="test"))
        hook_model.calls = []  # reset

        db.model(hook_model).find()

        assert "after_find" in hook_model.calls

    def test_before_create_can_modify_fields(self, db):
        class User(Model):
            __tablename__ = "prep_users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)

            def before_create(self):
                self.name = self.name.strip().upper()

        conn = db._session.connection
        conn.execute(SQLiteDialect().create_table_sql(User))
        conn.commit()

        u = User(name="  jinzhu  ")
        db.create(u)
        assert u.name == "JINZHU"
