from __future__ import annotations
import pytest
from gorm import open, Model, Field


class User(Model):
    __tablename__ = "users"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255, index=True)
    age: int = Field(default=18)


class TestIntegration:
    @pytest.fixture
    def db(self):
        db = open("sqlite://:memory:")
        db.auto_migrate(User)
        return db

    def test_full_crud_flow(self, db):
        # Create
        u = db.create(User(name="jinzhu", age=30))
        assert u.id == 1

        # Read
        found = db.where("id = ?", 1).first(User)
        assert found.name == "jinzhu"

        # Update
        db.model(User).where("id = ?", 1).update(name="jinzhu_new")
        found = db.where("id = ?", 1).first(User)
        assert found.name == "jinzhu_new"

        # Delete
        db.delete(found)
        assert db.model(User).count() == 0

    def test_chain_query(self, db):
        db.create(User(name="a", age=20))
        db.create(User(name="b", age=25))
        db.create(User(name="c", age=30))

        users = (
            db.model(User)
            .where("age >= ?", 20)
            .where("age <= ?", 30)
            .order("age ASC")
            .limit(2)
            .find()
        )
        assert len(users) == 2
        assert users[0].name == "a"
        assert users[1].name == "b"

    def test_open_in_memory(self, db):
        assert db.has_table(User) is True

    def test_exists(self, db):
        db.create(User(name="jinzhu"))
        assert db.model(User).where("name = ?", "jinzhu").exists() is True
        assert db.model(User).where("name = ?", "nobody").exists() is False


class TestSoftDelete:
    @pytest.fixture
    def product_model(self):
        class Product(Model):
            __tablename__ = "products"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)
            deleted_at: str | None = Field(soft_delete=True, nullable=True)

        return Product

    @pytest.fixture
    def db(self, product_model):
        from datetime import datetime
        from gorm import Config

        db = open(
            "sqlite://:memory:",
            Config(now_func=lambda: "2024-01-01T00:00:00"),
        )
        db.auto_migrate(product_model)
        return db

    def test_soft_delete_hides_deleted_records(self, db, product_model):
        db.create(product_model(name="p1"))
        db.create(product_model(name="p2"))

        # Soft delete p1
        p1 = db.where("name = ?", "p1").first(product_model)
        db.delete(p1)

        # p1 should be hidden
        all_products = db.model(product_model).find()
        assert len(all_products) == 1
        assert all_products[0].name == "p2"

    def test_unscoped_shows_soft_deleted_records(self, db, product_model):
        db.create(product_model(name="p1"))
        db.create(product_model(name="p2"))

        p1 = db.where("name = ?", "p1").first(product_model)
        db.delete(p1)

        all_products = db.model(product_model).unscoped().find()
        assert len(all_products) == 2

    def test_soft_delete_bulk(self, db, product_model):
        db.create(product_model(name="p1"))
        db.create(product_model(name="p2"))

        db.model(product_model).where("name = ?", "p1").delete()

        all_products = db.model(product_model).find()
        assert len(all_products) == 1
        assert all_products[0].name == "p2"

    def test_soft_delete_count_excludes_deleted(self, db, product_model):
        db.create(product_model(name="p1"))
        db.create(product_model(name="p2"))

        p1 = db.where("name = ?", "p1").first(product_model)
        db.delete(p1)

        cnt = db.model(product_model).count()
        assert cnt == 1


class TestLogger:
    def test_logger_with_custom_writer(self, user_model):
        logs: list[str] = []

        def capture(msg: str) -> None:
            logs.append(msg)

        from gorm import Config
        from gorm.logger import Logger

        logger = Logger(writer=capture)
        db = open("sqlite://:memory:", Config(logger=logger))
        db.auto_migrate(user_model)

        db.create(user_model(name="jinzhu", age=30))
        db.model(user_model).where("name = ?", "jinzhu").first()

        assert len(logs) >= 4  # migration check + create table + INSERT + SELECT
        assert any("INSERT" in l for l in logs)
        assert any("SELECT" in l for l in logs)
        assert all("[rows:" in l for l in logs)
        assert all("ms]" in l for l in logs)

    @pytest.fixture
    def user_model(self):
        class User(Model):
            __tablename__ = "log_users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)
            age: int = Field(default=18)

        return User
