import pytest
import sqlite3
import tempfile
import os
from gorm.db import DB
from gorm.model import Model
from gorm.field import Field
from gorm.dialects.sqlite import SQLiteDialect
from gorm.session import Session


class TestTransaction:
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

    def test_commit_persists_changes(self, db, user_model):
        tx = db.begin()
        tx.create(user_model(name="in_tx"))
        tx.commit()

        users = db.model(user_model).find()
        assert len(users) == 1
        assert users[0].name == "in_tx"

    def test_rollback_discards_changes(self, db, user_model):
        tx = db.begin()
        tx.create(user_model(name="will_rollback"))
        tx.rollback()

        users = db.model(user_model).find()
        assert len(users) == 0

    def test_transaction_closure_commits_on_success(self, db, user_model):
        def do_work(tx):
            tx.create(user_model(name="closure_a"))
            tx.create(user_model(name="closure_b"))

        db.transaction(do_work)

        users = db.model(user_model).find()
        assert len(users) == 2

    def test_transaction_closure_rolls_back_on_exception(self, db, user_model):
        def do_work(tx):
            tx.create(user_model(name="closure_a"))
            raise ValueError("something went wrong")

        with pytest.raises(ValueError, match="something went wrong"):
            db.transaction(do_work)

        users = db.model(user_model).find()
        assert len(users) == 0

    def test_transaction_isolation(self, db, user_model):
        """Uncommitted changes in tx are not visible from outside the tx session."""
        # Use a temp file-based DB so two connections share the same database
        tmpfile = tempfile.mktemp(suffix=".db")
        try:
            conn1 = sqlite3.connect(tmpfile)
            conn1.row_factory = sqlite3.Row
            dialect = SQLiteDialect()
            session1 = Session(conn1, dialect)
            create_sql = dialect.create_table_sql(user_model)
            conn1.execute(create_sql)
            conn1.commit()
            db1 = DB(dialect=dialect, session=session1, config=None)

            tx = db1.begin()
            tx.create(user_model(name="tx_only"))

            # Separate connection should not see the uncommitted change
            conn2 = sqlite3.connect(tmpfile)
            conn2.row_factory = sqlite3.Row
            session2 = Session(conn2, dialect)
            db2 = DB(dialect=dialect, session=session2, config=None)

            users = db2.model(user_model).find()
            assert len(users) == 0

            tx.commit()

            # After commit, both connections can see it
            users = db1.model(user_model).find()
            assert len(users) == 1
            users = db2.model(user_model).find()
            assert len(users) == 1
        finally:
            try:
                conn1.close()
            except Exception:
                pass
            try:
                conn2.close()
            except Exception:
                pass
            try:
                os.unlink(tmpfile)
            except Exception:
                pass
