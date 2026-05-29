from __future__ import annotations
import pytest
import sqlite3
from gorm.db import DB
from gorm.model import Model
from gorm.field import Field
from gorm.dialects.sqlite import SQLiteDialect
from gorm.session import Session


class TestManyToMany:
    @pytest.fixture
    def models(self):
        class User(Model):
            __tablename__ = "users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)
            languages: list[Language] = Field(many_to_many="Language")

        class Language(Model):
            __tablename__ = "languages"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)

        return User, Language

    @pytest.fixture
    def db(self, models):
        User, Language = models
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        dialect = SQLiteDialect()
        session = Session(conn, dialect)
        conn.execute(dialect.create_table_sql(User))
        conn.execute(dialect.create_table_sql(Language))
        # Create junction table manually
        conn.execute(
            'CREATE TABLE IF NOT EXISTS "languages_users" ('
            '  "user_id" INTEGER NOT NULL,'
            '  "language_id" INTEGER NOT NULL,'
            '  PRIMARY KEY ("user_id", "language_id")'
            ')'
        )
        conn.commit()
        return DB(dialect=dialect, session=session, config=None)

    def test_many_to_many_find(self, db, models):
        User, Language = models
        u = db.create(User(name="jinzhu"))
        py = db.create(Language(name="Python"))
        js = db.create(Language(name="JavaScript"))

        # Insert junction rows
        db.raw(
            'INSERT INTO "languages_users" ("user_id", "language_id") VALUES (?, ?)', u.id, py.id
        )
        db.raw(
            'INSERT INTO "languages_users" ("user_id", "language_id") VALUES (?, ?)', u.id, js.id
        )

        langs = db.model(u).association("languages").find()
        assert len(langs) == 2
        assert langs[0].name == "Python"
        assert langs[1].name == "JavaScript"

    def test_many_to_many_empty(self, db, models):
        User, Language = models
        u = db.create(User(name="alone"))

        langs = db.model(u).association("languages").find()
        assert langs == []

    def test_many_to_many_preload(self, db, models):
        User, Language = models
        u1 = db.create(User(name="alice"))
        u2 = db.create(User(name="bob"))
        py = db.create(Language(name="Python"))
        js = db.create(Language(name="JavaScript"))
        go = db.create(Language(name="Go"))

        db.raw('INSERT INTO "languages_users" VALUES (?, ?)', u1.id, py.id)
        db.raw('INSERT INTO "languages_users" VALUES (?, ?)', u1.id, js.id)
        db.raw('INSERT INTO "languages_users" VALUES (?, ?)', u2.id, go.id)

        users = db.preload("languages").find(User)
        assert len(users) == 2
        assert len(users[0].languages) == 2
        assert len(users[1].languages) == 1


class TestManyToManyAutoMigrate:
    def test_auto_migrate_creates_junction_table(self):
        from gorm import open

        class User(Model):
            __tablename__ = "users"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)
            roles: list[Role] = Field(many_to_many="Role")

        class Role(Model):
            __tablename__ = "roles"
            id: int = Field(primary_key=True, auto_increment=True)
            name: str = Field(size=255)

        db = open("sqlite://:memory:")
        db.auto_migrate(User, Role)

        # VT should exist
        rows = db.raw(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            "roles_users",
        )
        assert len(rows) == 1
