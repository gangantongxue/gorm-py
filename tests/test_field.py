import pytest
from gorm.field import Field, FieldMeta, Expression
from gorm.dialects.sqlite import SQLiteDialect


class TestFieldMeta:
    def test_default_values(self):
        meta = FieldMeta(column_name="name", python_type=str)
        assert meta.column_name == "name"
        assert meta.python_type is str
        assert meta.primary_key is False
        assert meta.auto_increment is False
        assert meta.default is None
        assert meta.unique is False
        assert meta.index is False
        assert meta.nullable is False
        assert meta.size == 0
        assert meta.auto_now is False
        assert meta.auto_now_add is False
        assert meta.comment == ""

    def test_custom_values(self):
        meta = FieldMeta(
            column_name="uid",
            python_type=int,
            primary_key=True,
            auto_increment=True,
            default=0,
            unique=True,
            index=True,
            nullable=True,
            size=64,
            comment="user id",
        )
        assert meta.primary_key is True
        assert meta.auto_increment is True
        assert meta.default == 0
        assert meta.unique is True
        assert meta.index is True
        assert meta.nullable is True
        assert meta.size == 64
        assert meta.comment == "user id"


class TestField:
    def test_field_stores_kwargs_as_meta(self):
        f = Field(primary_key=True, size=255, default="")
        meta = f._meta(column_name="username", python_type=str)
        assert meta.primary_key is True
        assert meta.size == 255
        assert meta.default == ""

    def test_field_meta_merges_column_name_and_type(self):
        f = Field(unique=True)
        meta = f._meta(column_name="email", python_type=str)
        assert meta.column_name == "email"
        assert meta.python_type is str
        assert meta.unique is True


class TestLambdaExpressions:
    @pytest.fixture
    def dialect(self):
        return SQLiteDialect()

    def test_eq_expression(self, dialect):
        f = Field(size=255)
        f.__set_name__(type("Dummy", (), {}), "name")
        expr = f == "jinzhu"
        sql, params = expr.compile(dialect)
        assert sql == '"name" = ?'
        assert params == ["jinzhu"]

    def test_gt_expression(self, dialect):
        f = Field()
        f.__set_name__(type("Dummy", (), {}), "age")
        expr = f > 18
        sql, params = expr.compile(dialect)
        assert sql == '"age" > ?'
        assert params == [18]

    def test_ge_expression(self, dialect):
        f = Field()
        f.__set_name__(type("Dummy", (), {}), "age")
        expr = f >= 18
        sql, params = expr.compile(dialect)
        assert sql == '"age" >= ?'
        assert params == [18]

    def test_lt_expression(self, dialect):
        f = Field()
        f.__set_name__(type("Dummy", (), {}), "age")
        expr = f < 65
        sql, params = expr.compile(dialect)
        assert sql == '"age" < ?'
        assert params == [65]

    def test_le_expression(self, dialect):
        f = Field()
        f.__set_name__(type("Dummy", (), {}), "age")
        expr = f <= 65
        sql, params = expr.compile(dialect)
        assert sql == '"age" <= ?'
        assert params == [65]

    def test_ne_expression(self, dialect):
        f = Field()
        f.__set_name__(type("Dummy", (), {}), "status")
        expr = f != "deleted"
        sql, params = expr.compile(dialect)
        assert sql == '"status" != ?'
        assert params == ["deleted"]

    def test_is_null_expression(self, dialect):
        f = Field()
        f.__set_name__(type("Dummy", (), {}), "deleted_at")
        expr = f == None
        sql, params = expr.compile(dialect)
        assert sql == '"deleted_at" IS NULL'
        assert params == []

    def test_is_not_null_expression(self, dialect):
        f = Field()
        f.__set_name__(type("Dummy", (), {}), "email")
        expr = f != None
        sql, params = expr.compile(dialect)
        assert sql == '"email" IS NOT NULL'
        assert params == []

    def test_and_expression(self, dialect):
        f1 = Field()
        f1.__set_name__(type("Dummy", (), {}), "age")
        f2 = Field()
        f2.__set_name__(type("Dummy", (), {}), "status")
        expr = (f1 > 18) & (f2 == "active")
        sql, params = expr.compile(dialect)
        assert sql == '"age" > ? AND "status" = ?'
        assert params == [18, "active"]

    def test_or_expression(self, dialect):
        f1 = Field()
        f1.__set_name__(type("Dummy", (), {}), "status")
        f2 = Field()
        f2.__set_name__(type("Dummy", (), {}), "status")
        expr = (f1 == "active") | (f2 == "pending")
        sql, params = expr.compile(dialect)
        assert sql == '"status" = ? OR "status" = ?'
        assert params == ["active", "pending"]

    def test_like_expression(self, dialect):
        f = Field()
        f.__set_name__(type("Dummy", (), {}), "name")
        expr = f.like("%jinzhu%")
        sql, params = expr.compile(dialect)
        assert sql == '"name" LIKE ?'
        assert params == ["%jinzhu%"]

    def test_in_expression(self, dialect):
        f = Field()
        f.__set_name__(type("Dummy", (), {}), "id")
        expr = f.in_([1, 2, 3])
        sql, params = expr.compile(dialect)
        assert sql == '"id" IN (?, ?, ?)'
        assert params == [1, 2, 3]

    def test_between_expression(self, dialect):
        f = Field()
        f.__set_name__(type("Dummy", (), {}), "age")
        expr = f.between(18, 65)
        sql, params = expr.compile(dialect)
        assert sql == '"age" BETWEEN ? AND ?'
        assert params == [18, 65]


class TestLambdaDB:
    """Integration tests for lambda expressions with DB."""
    def test_lambda_where_in_db(self):
        import sqlite3
        from gorm.db import DB
        from gorm.model import Model
        from gorm.field import Field
        from gorm.dialects.sqlite import SQLiteDialect
        from gorm.session import Session

        class User(Model):
            __tablename__ = "users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)
            age: int = Field(default=18)

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        dialect = SQLiteDialect()
        session = Session(conn, dialect)
        conn.execute(dialect.create_table_sql(User))
        conn.commit()
        db = DB(dialect=dialect, session=session, config=None)

        db.create(User(name="jinzhu", age=30))
        db.create(User(name="bob", age=25))

        # Lambda where
        users = db.model(User).where(User.name == "jinzhu").find()
        assert len(users) == 1
        assert users[0].age == 30

        # Combined lambda + string
        users = db.model(User).where(User.age > 20).where("name != ?", "jinzhu").find()
        assert len(users) == 1
        assert users[0].name == "bob"

        # AND expression
        users = db.model(User).where((User.age > 20) & (User.name == "jinzhu")).find()
        assert len(users) == 1

        # Lambda with count
        cnt = db.model(User).where(User.age >= 18).count()
        assert cnt == 2
