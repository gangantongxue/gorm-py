import pytest
import sqlite3
from gorm.db import DB
from gorm.model import Model
from gorm.field import Field
from gorm.dialects.sqlite import SQLiteDialect
from gorm.session import Session


class TestDBCreateAndFind:
    @pytest.fixture
    def user_model(self):
        class User(Model):
            __tablename__ = "users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)
            age: int = Field(default=18)

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

    def test_create_and_find_all(self, db, user_model):
        u = user_model(name="jinzhu", age=30)
        db.create(u)

        users = db.model(user_model).find()
        assert len(users) == 1
        assert users[0].name == "jinzhu"
        assert users[0].age == 30
        assert users[0].id == 1

    def test_create_returns_back_pk(self, db, user_model):
        u = user_model(name="alice")
        result = db.create(u)
        assert u.id == 1

    def test_first_returns_first_match(self, db, user_model):
        db.create(user_model(name="a", age=20))
        db.create(user_model(name="b", age=25))

        u = db.model(user_model).where("name = ?", "a").first()
        assert u is not None
        assert u.name == "a"

    def test_first_returns_none_when_no_match(self, db, user_model):
        u = db.model(user_model).where("name = ?", "nobody").first()
        assert u is None

    def test_where_chaining(self, db, user_model):
        db.create(user_model(name="a", age=20))
        db.create(user_model(name="b", age=30))
        db.create(user_model(name="c", age=30))

        users = db.model(user_model).where("age = ?", 30).where("name != ?", "b").find()
        assert len(users) == 1
        assert users[0].name == "c"

    def test_order_and_limit(self, db, user_model):
        db.create(user_model(name="c", age=10))
        db.create(user_model(name="a", age=20))
        db.create(user_model(name="b", age=30))

        users = db.model(user_model).order("name ASC").limit(2).find()
        assert len(users) == 2
        assert users[0].name == "a"
        assert users[1].name == "b"

    def test_count(self, db, user_model):
        db.create(user_model(name="a", age=20))
        db.create(user_model(name="b", age=30))

        cnt = db.model(user_model).where("age > ?", 10).count()
        assert cnt == 2

        cnt2 = db.model(user_model).where("age > ?", 50).count()
        assert cnt2 == 0

    def test_select_specific_columns(self, db, user_model):
        db.create(user_model(name="jinzhu", age=30))

        u = db.model(user_model).select("name").first()
        assert u is not None
        assert u.name == "jinzhu"
        assert u.age == 18

    def test_in_memory_db_isolated(self, user_model):
        conn1 = sqlite3.connect(":memory:")
        conn1.row_factory = sqlite3.Row
        conn2 = sqlite3.connect(":memory:")
        conn2.row_factory = sqlite3.Row

        dialect = SQLiteDialect()
        db1 = DB(dialect=dialect, session=Session(conn1, dialect), config=None)
        db2 = DB(dialect=dialect, session=Session(conn2, dialect), config=None)

        create_sql = dialect.create_table_sql(user_model)
        conn1.execute(create_sql)
        conn1.commit()
        conn2.execute(create_sql)
        conn2.commit()

        db1.create(user_model(name="from_db1"))
        db2.create(user_model(name="from_db2"))

        assert len(db1.model(user_model).find()) == 1
        assert len(db2.model(user_model).find()) == 1


class TestDBUpdateDelete:
    @pytest.fixture
    def user_model(self):
        class User(Model):
            __tablename__ = "users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)
            age: int = Field(default=18)

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

    def test_update_by_condition(self, db, user_model):
        db.create(user_model(name="jinzhu", age=30))
        db.create(user_model(name="bob", age=25))

        affected = db.model(user_model).where("name = ?", "jinzhu").update(name="jinzhu_new", age=31)
        assert affected == 1

        u = db.model(user_model).where("name = ?", "jinzhu_new").first()
        assert u is not None
        assert u.age == 31

        # bob should be unchanged
        u2 = db.model(user_model).where("name = ?", "bob").first()
        assert u2.age == 25

    def test_update_without_where_updates_all(self, db, user_model):
        db.create(user_model(name="a", age=10))
        db.create(user_model(name="b", age=20))

        affected = db.model(user_model).update(age=0)
        assert affected == 2

        users = db.model(user_model).find()
        assert all(u.age == 0 for u in users)

    def test_delete_by_condition(self, db, user_model):
        db.create(user_model(name="jinzhu"))
        db.create(user_model(name="bob"))

        affected = db.model(user_model).where("name = ?", "jinzhu").delete()
        assert affected == 1

        users = db.model(user_model).find()
        assert len(users) == 1
        assert users[0].name == "bob"

    def test_delete_by_instance(self, db, user_model):
        u = db.create(user_model(name="jinzhu"))

        db.delete(u)
        users = db.model(user_model).find()
        assert len(users) == 0

    def test_save_inserts_new_record(self, db, user_model):
        u = user_model(name="new_user", age=25)
        db.save(u)

        assert u.id is not None
        found = db.model(user_model).where("name = ?", "new_user").first()
        assert found is not None

    def test_save_updates_existing_record(self, db, user_model):
        u = db.create(user_model(name="jinzhu", age=30))
        u.name = "jinzhu_updated"
        u.age = 31
        db.save(u)

        found = db.model(user_model).where("id = ?", u.id).first()
        assert found.name == "jinzhu_updated"
        assert found.age == 31

    def test_delete_all(self, db, user_model):
        db.create(user_model(name="a"))
        db.create(user_model(name="b"))

        affected = db.model(user_model).delete()
        assert affected == 2
        assert db.model(user_model).count() == 0


class TestDBScopes:
    @pytest.fixture
    def user_model(self):
        class User(Model):
            __tablename__ = "users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)
            age: int = Field(default=18)
            status: str = Field(size=50, default="active")

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

    def test_single_scope(self, db, user_model):
        db.create(user_model(name="jinzhu", age=30, status="active"))
        db.create(user_model(name="bob", age=25, status="inactive"))

        def active(db_):
            return db_.where("status = ?", "active")

        users = db.scopes(active).model(user_model).find()
        assert len(users) == 1
        assert users[0].name == "jinzhu"

    def test_multiple_scopes(self, db, user_model):
        db.create(user_model(name="jinzhu", age=30, status="active"))
        db.create(user_model(name="alice", age=22, status="active"))
        db.create(user_model(name="bob", age=25, status="inactive"))

        def active(db_):
            return db_.where("status = ?", "active")

        def adults(db_):
            return db_.where("age >= ?", 25)

        users = db.scopes(active, adults).model(user_model).find()
        assert len(users) == 1
        assert users[0].name == "jinzhu"

    def test_scope_with_parameter(self, db, user_model):
        db.create(user_model(name="p1", age=10))
        db.create(user_model(name="p2", age=20))
        db.create(user_model(name="p3", age=30))
        db.create(user_model(name="p4", age=40))
        db.create(user_model(name="p5", age=50))

        def paginate(page, page_size):
            def scope(db_):
                return db_.offset((page - 1) * page_size).limit(page_size)
            return scope

        users = db.scopes(paginate(2, 2)).model(user_model).order("age ASC").find()
        assert len(users) == 2
        assert users[0].name == "p3"
        assert users[1].name == "p4"
