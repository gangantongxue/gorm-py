import pytest
from gorm.query import Query
from gorm.model import Model
from gorm.field import Field
from gorm.dialects.sqlite import SQLiteDialect


class TestQueryCompilation:
    @pytest.fixture
    def dialect(self):
        return SQLiteDialect()

    @pytest.fixture
    def user_model(self):
        class User(Model):
            __tablename__ = "users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)
            age: int = Field(default=18)

        return User

    def test_select_all(self, dialect, user_model):
        q = Query(table=user_model.__tablename__)
        sql, params = q.compile_select(dialect)
        assert 'SELECT * FROM "users"' == sql
        assert params == []

    def test_select_with_where(self, dialect, user_model):
        q = Query(table=user_model.__tablename__)
        q.add_where("name = ?", ["jinzhu"])
        q.add_where("age > ?", [18])
        sql, params = q.compile_select(dialect)
        assert 'SELECT * FROM "users" WHERE name = ? AND age > ?' == sql
        assert params == ["jinzhu", 18]

    def test_select_with_order_and_limit(self, dialect, user_model):
        q = Query(table=user_model.__tablename__)
        q.add_order("id DESC")
        q.set_limit(10)
        q.set_offset(5)
        sql, params = q.compile_select(dialect)
        assert 'SELECT * FROM "users" ORDER BY id DESC LIMIT 10 OFFSET 5' == sql

    def test_select_with_specific_columns(self, dialect, user_model):
        q = Query(table=user_model.__tablename__)
        q.set_select(['"id"', '"name"'])
        sql, params = q.compile_select(dialect)
        assert 'SELECT "id", "name" FROM "users"' == sql

    def test_select_count(self, dialect, user_model):
        q = Query(table=user_model.__tablename__)
        q.set_count_mode(True)
        sql, params = q.compile_select(dialect)
        assert 'SELECT COUNT(*) FROM "users"' == sql

    def test_select_with_or_where(self, dialect, user_model):
        q = Query(table=user_model.__tablename__)
        q.add_where("name = ?", ["jinzhu"])
        q.add_or_where("name = ?", ["bob"])
        sql, params = q.compile_select(dialect)
        assert 'SELECT * FROM "users" WHERE name = ? OR name = ?' == sql
        assert params == ["jinzhu", "bob"]

    def test_select_with_not(self, dialect, user_model):
        q = Query(table=user_model.__tablename__)
        q.add_where("age > ?", [18])
        q.add_not("name = ?", ["jinzhu"])
        sql, params = q.compile_select(dialect)
        assert "NOT name = ?" in sql

    def test_insert(self, dialect, user_model):
        q = Query(table=user_model.__tablename__)
        sql, params = q.compile_insert(
            fields=["name", "age"],
            values=["jinzhu", 30],
            dialect=dialect,
        )
        assert 'INSERT INTO "users" ("name", "age") VALUES (?, ?)' == sql
        assert params == ["jinzhu", 30]

    def test_update(self, dialect, user_model):
        q = Query(table=user_model.__tablename__)
        q.add_where("id = ?", [1])
        sql, params = q.compile_update(
            updates={"name": "new_name", "age": 31},
            dialect=dialect,
        )
        assert 'UPDATE "users" SET "name"=?, "age"=? WHERE id = ?' == sql
        assert params == ["new_name", 31, 1]

    def test_delete(self, dialect, user_model):
        q = Query(table=user_model.__tablename__)
        q.add_where("id = ?", [1])
        sql, params = q.compile_delete(dialect)
        assert 'DELETE FROM "users" WHERE id = ?' == sql
        assert params == [1]

    def test_clone_produces_independent_copy(self, dialect, user_model):
        q1 = Query(table=user_model.__tablename__)
        q1.add_where("age > ?", [18])

        q2 = q1.clone()
        q2.add_where("name = ?", ["jinzhu"])

        sql1, params1 = q1.compile_select(dialect)
        assert params1 == [18]

        sql2, params2 = q2.compile_select(dialect)
        assert params2 == [18, "jinzhu"]
