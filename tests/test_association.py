from __future__ import annotations
import pytest
import sqlite3
from gorm.db import DB
from gorm.model import Model
from gorm.field import Field
from gorm.dialects.sqlite import SQLiteDialect
from gorm.session import Session


class TestBelongsTo:
    @pytest.fixture
    def models(self):
        class Company(Model):
            __tablename__ = "companies"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)

        class User(Model):
            __tablename__ = "users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)
            company_id: int = Field(nullable=True)
            company: Company = Field(belongs_to="Company")

        return Company, User

    @pytest.fixture
    def db(self, models):
        Company, User = models
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        dialect = SQLiteDialect()
        session = Session(conn, dialect)
        conn.execute(dialect.create_table_sql(Company))
        conn.execute(dialect.create_table_sql(User))
        conn.commit()
        return DB(dialect=dialect, session=session, config=None)

    def test_belongs_to_find(self, db, models):
        Company, User = models
        c = db.create(Company(name="Acme Corp"))
        u = db.create(User(name="jinzhu", company_id=c.id))

        loaded_company = db.model(u).association("company").find()
        assert loaded_company is not None
        assert loaded_company.name == "Acme Corp"
        assert loaded_company.id == c.id

    def test_belongs_to_returns_none_when_fk_null(self, db, models):
        Company, User = models
        u = db.create(User(name="jinzhu", company_id=None))

        loaded_company = db.model(u).association("company").find()
        assert loaded_company is None

    def test_belongs_to_preload(self, db, models):
        Company, User = models
        c1 = db.create(Company(name="Acme Corp"))
        c2 = db.create(Company(name="Globex"))
        db.create(User(name="alice", company_id=c1.id))
        db.create(User(name="bob", company_id=c2.id))
        db.create(User(name="charlie", company_id=None))

        users = db.preload("company").find(User)
        assert len(users) == 3
        assert users[0].company is not None
        assert users[0].company.name == "Acme Corp"
        assert users[1].company is not None
        assert users[1].company.name == "Globex"
        assert users[2].company is None


class TestHasMany:
    @pytest.fixture
    def models(self):
        class User(Model):
            __tablename__ = "users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)
            orders: list[Order] = Field(has_many="Order")

        class Order(Model):
            __tablename__ = "orders"
            id: int = Field(primary_key=True, auto_increment=True)
            user_id: int = Field()
            amount: float = Field()

        return User, Order

    @pytest.fixture
    def db(self, models):
        User, Order = models
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        dialect = SQLiteDialect()
        session = Session(conn, dialect)
        conn.execute(dialect.create_table_sql(User))
        conn.execute(dialect.create_table_sql(Order))
        conn.commit()
        return DB(dialect=dialect, session=session, config=None)

    def test_has_many_find(self, db, models):
        User, Order = models
        u = db.create(User(name="jinzhu"))
        from gorm.db import DB as _
        db.create(Order(user_id=u.id, amount=10.0))
        db.create(Order(user_id=u.id, amount=20.0))
        db.create(Order(user_id=999, amount=99.0))

        orders = db.model(u).association("orders").find()
        assert len(orders) == 2
        assert orders[0].amount == 10.0
        assert orders[1].amount == 20.0

    def test_has_many_empty(self, db, models):
        User, Order = models
        u = db.create(User(name="jinzhu"))

        orders = db.model(u).association("orders").find()
        assert orders == []

    def test_has_many_preload(self, db, models):
        User, Order = models
        u1 = db.create(User(name="alice"))
        u2 = db.create(User(name="bob"))
        db.create(Order(user_id=u1.id, amount=10.0))
        db.create(Order(user_id=u1.id, amount=20.0))
        db.create(Order(user_id=u2.id, amount=30.0))

        users = db.preload("orders").find(User)
        assert len(users) == 2
        assert len(users[0].orders) == 2
        assert len(users[1].orders) == 1
        assert users[0].orders[0].amount == 10.0
        assert users[0].orders[1].amount == 20.0
        assert users[1].orders[0].amount == 30.0

    def test_has_many_preload_empty(self, db, models):
        User, Order = models
        u = db.create(User(name="alone"))
        db.create(User(name="also_alone"))

        users = db.preload("orders").find(User)
        assert len(users) == 2
        assert users[0].orders == []
        assert users[1].orders == []

    def test_has_many_with_foreign_key(self, db, models):
        User, Order = models
        u = db.create(User(name="jinzhu"))
        db.create(Order(user_id=u.id, amount=42.0))

        orders = db.model(u).association("orders").find()
        assert len(orders) == 1


class TestAssociationDB:
    """Integration test using public API for associations."""
    def test_full_association_flow(self):
        from gorm import open

        class Company(Model):
            __tablename__ = "companies"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)

        class User(Model):
            __tablename__ = "users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)
            company_id: int = Field(nullable=True)
            company: Company = Field(belongs_to=Company)

        db = open("sqlite://:memory:")
        db.auto_migrate(Company, User)

        c = db.create(Company(name="Acme Corp"))
        u = db.create(User(name="jinzhu", company_id=c.id))

        # Association find
        loaded = db.model(u).association("company").find()
        assert loaded.name == "Acme Corp"

        # Preload
        users = db.preload("company").find(User)
        assert users[0].company.name == "Acme Corp"
