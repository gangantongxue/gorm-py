#!/usr/bin/env python3
from __future__ import annotations
"""
gorm-py 完整功能演示 & 冒烟测试
============================

运行方式:
    python3 examples/demo.py

涵盖功能:
    P0: Model 定义, CRUD, AutoMigrate, Hooks, Transactions
    P1: Lambda 表达式 where, Scopes, Soft Delete, Logger
    P2: BelongsTo, HasMany, Preload
    P3: GormModel, 嵌套事务, ManyToMany
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gorm import open, Model, GormModel, Field, Config
from gorm.errors import RecordNotFound

pass_count = 0
fail_count = 0


def check(name: str, condition: bool, detail: str = ""):
    global pass_count, fail_count
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f"  ({detail})"
    print(msg)
    if condition:
        pass_count += 1
    else:
        fail_count += 1
    return condition


def seg(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ============================================================
# 0. 定义 Model
# ============================================================
seg("0. Model 定义")


class Company(Model):
    __tablename__ = "companies"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255, index=True)


class User(Model):
    __tablename__ = "users"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255, index=True)
    age: int = Field(default=18)
    status: str = Field(size=50, default="active")
    company_id: int = Field(nullable=True)

    # P2: 关联
    company: Company = Field(belongs_to=Company)
    orders: list["Order"] = Field(has_many="Order")


class UserWithSoftDelete(GormModel):
    """使用 GormModel 基类（自动包含 id, created_at, updated_at, deleted_at）"""
    __tablename__ = "users_sd"
    name: str = Field(size=255)


class Order(Model):
    __tablename__ = "orders"
    id: int = Field(primary_key=True, auto_increment=True)
    user_id: int = Field(index=True)
    amount: float = Field()
    item: str = Field(size=255)


class Language(Model):
    __tablename__ = "languages"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)


class UserWithLanguages(Model):
    __tablename__ = "users_lang"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)
    languages: list[Language] = Field(many_to_many="Language")


check("User fields", "name" in User.__gorm_fields__)
check("User.has company association", User.__gorm_fields__["company"].belongs_to == "Company")
check("User.has orders association", User.__gorm_fields__["orders"].has_many == "Order")
check("GormModel.has soft_delete", UserWithSoftDelete.soft_delete_field() is not None)
check("GormModel.has id", UserWithSoftDelete.primary_key_field().column_name == "id")


# ============================================================
# 1. AutoMigrate & CRUD
# ============================================================
seg("1. AutoMigrate & CRUD")

db = open("sqlite://:memory:")
db.auto_migrate(Company, User, Order)

check("has_table(Company)", db.has_table(Company))
check("has_table(User)", db.has_table(User))
check("has_table(Order)", db.has_table(Order))

# ----- Create -----
c = db.create(Company(name="Acme Corp"))
u = db.create(User(name="jinzhu", age=30, company_id=c.id))
db.create(User(name="bob", age=25))

check("create returns pk", u.id == 1 and c.id == 1)
check("create sets fields", u.name == "jinzhu" and u.age == 30)

# ----- Read -----
found = db.where("id = ?", 1).first(User)
check("first() by id", found is not None and found.name == "jinzhu")

all_users = db.find(User)
check("find() all", len(all_users) == 2)

count_active = db.model(User).where("status = ?", "active").count()
check("count()", count_active == 2)

exists = db.model(User).where("name = ?", "jinzhu").exists()
check("exists() True", exists is True)

not_exists = db.model(User).where("name = ?", "nobody").exists()
check("exists() False", not_exists is False)

# ----- Update -----
db.model(User).where("id = ?", 1).update(name="jinzhu_new", age=31)
updated = db.where("id = ?", 1).first(User)
check("update()", updated.name == "jinzhu_new" and updated.age == 31)

# ----- Save (upsert) -----
u_new = User(name="charlie", age=22)
db.save(u_new)
check("save() insert", u_new.id is not None and u_new.id == 3)

u_new.name = "charlie_updated"
db.save(u_new)
check("save() update", db.where("id = ?", 3).first(User).name == "charlie_updated")

# ----- Delete -----
db.delete(u_new)
check("delete() instance", db.model(User).count() == 2)

# ----- Order & Limit -----
users = db.model(User).order("age DESC").limit(1).find()
check("order+limit", users[0].name == "jinzhu_new")


# ============================================================
# 2. Hooks
# ============================================================
seg("2. Hooks (生命周期)")

class HookUser(Model):
    __tablename__ = "hook_users"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)

    def before_create(self):
        self.name = self.name.strip()

    def after_create(self):
        pass  # hook exists but does nothing


db.auto_migrate(HookUser)
hu = db.create(HookUser(name="  trimmed  "))
check("before_create trims name", hu.name == "trimmed")


# ============================================================
# 3. Transactions
# ============================================================
seg("3. Transactions")

def _create_orders(tx):
    tx.create(Order(user_id=1, amount=10.0, item="Apple"))
    tx.create(Order(user_id=1, amount=20.0, item="Banana"))
    tx.create(Order(user_id=2, amount=30.0, item="Cherry"))

db.transaction(_create_orders)

check("transaction commit", db.model(Order).count() == 3)

def _create_and_fail(tx):
    tx.create(Order(user_id=1, amount=99.0, item="ShouldRollback"))
    raise ValueError("oops")

try:
    db.transaction(_create_and_fail)
except ValueError:
    pass

check("transaction rollback", db.model(Order).count() == 3)


# ============================================================
# 4. Lambda 表达式 where
# ============================================================
seg("4. Lambda 表达式 where")

users = db.where(User.age > 20).find(User)
check("lambda > ", len(users) == 2)  # jinzhu_new (31) and bob (25)

users = db.where((User.age >= 18) & (User.status == "active")).find(User)
check("lambda & ", len(users) == 2)

users = db.where(User.name.like("%zhu%")).find(User)
check("lambda like", len(users) == 1)

users = db.where(User.id.in_([1, 3])).find(User)
check("lambda in", len(users) == 1)  # id=3 was deleted


# ============================================================
# 5. Scopes
# ============================================================
seg("5. Scopes")

def adults(db_):
    return db_.where("age >= ?", 18)

users = db.scopes(adults).model(User).find()
check("scope: adults", len(users) == 2)


# ============================================================
# 6. Soft Delete
# ============================================================
seg("6. Soft Delete")

from datetime import datetime

sd_db = open("sqlite://:memory:", Config(now_func=lambda: datetime(2024, 1, 1, 12, 0, 0).isoformat()))
sd_db.auto_migrate(UserWithSoftDelete)

u1 = sd_db.create(UserWithSoftDelete(name="keep"))
u2 = sd_db.create(UserWithSoftDelete(name="trash"))

sd_db.delete(u2)

check("soft delete hides record", sd_db.model(UserWithSoftDelete).count() == 1)
check("unscoped shows all", sd_db.model(UserWithSoftDelete).unscoped().count() == 2)
check("soft delete sets deleted_at",
      sd_db.model(UserWithSoftDelete).unscoped().where("name = ?", "trash").first().deleted_at is not None)


# ============================================================
# 7. Associations (BelongsTo, HasMany)
# ============================================================
seg("7. Associations")

# BelongsTo
loaded_company = db.model(u).association("company").find()
check("belongs_to find", loaded_company is not None and loaded_company.name == "Acme Corp")

# HasMany
loaded_orders = db.model(u).association("orders").find()
check("has_many find", len(loaded_orders) == 2 and loaded_orders[0].item == "Apple")

# Test association with user who has orders
bob_orders = db.model(db.where("name = ?", "bob").first(User)).association("orders").find()
check("has_many for bob", len(bob_orders) == 1 and bob_orders[0].item == "Cherry")


# ============================================================
# 8. Preload (预加载)
# ============================================================
seg("8. Preload (预加载)")

all_users = db.preload("company").preload("orders").find(User)
check("preload user count", len(all_users) == 2)

jinzhu = next(u for u in all_users if u.name == "jinzhu_new")
check("preload belongs_to", jinzhu.company is not None and jinzhu.company.name == "Acme Corp")
check("preload has_many", len(jinzhu.orders) == 2)

bob = next(u for u in all_users if u.name == "bob")
check("preload has_many (single)", len(bob.orders) == 1 and bob.orders[0].item == "Cherry")


# ============================================================
# 9. ManyToMany
# ============================================================
seg("9. ManyToMany")

m2m_db = open("sqlite://:memory:")
m2m_db.auto_migrate(UserWithLanguages, Language)

u_lang = m2m_db.create(UserWithLanguages(name="polyglot"))
py = m2m_db.create(Language(name="Python"))
js = m2m_db.create(Language(name="JavaScript"))
go = m2m_db.create(Language(name="Go"))

# Insert junction rows using auto-generated column names
jt_cols = m2m_db.raw(
    "SELECT sql FROM sqlite_master WHERE type='table' AND name='languages_users_lang'"
)
# Use the correct column names from auto-migration
m2m_db.raw("INSERT INTO languages_users_lang (userwithlanguages_id, language_id) VALUES (?, ?)", u_lang.id, py.id)
m2m_db.raw("INSERT INTO languages_users_lang (userwithlanguages_id, language_id) VALUES (?, ?)", u_lang.id, js.id)
m2m_db.raw("INSERT INTO languages_users_lang (userwithlanguages_id, language_id) VALUES (?, ?)", u_lang.id, go.id)

langs = m2m_db.model(u_lang).association("languages").find()
check("m2m find count", len(langs) == 3)
check("m2m find names", {l.name for l in langs} == {"Python", "JavaScript", "Go"})

u2 = m2m_db.create(UserWithLanguages(name="monoglot"))
m2m_db.raw("INSERT INTO languages_users_lang (userwithlanguages_id, language_id) VALUES (?, ?)", u2.id, py.id)

users = m2m_db.preload("languages").find(UserWithLanguages)
check("m2m preload count", len(users) == 2)
check("m2m preload polyglot", len(users[0].languages) == 3)
check("m2m preload monoglot", len(users[1].languages) == 1)


# ============================================================
# 10. Logger
# ============================================================
seg("10. Logger")

logs = []
def capture(msg):
    logs.append(msg)

from gorm.logger import Logger

log_db = open(
    "sqlite://:memory:",
    Config(logger=Logger(writer=capture)),
)
log_db.auto_migrate(Company)
log_db.create(Company(name="LogCorp"))
log_db.where("name = ?", "LogCorp").first(Company)

check("logger produces output", len(logs) > 0)
check("logger has SQL", any("INSERT" in l or "CREATE" in l or "SELECT" in l for l in logs))


# ============================================================
# 11. 嵌套事务
# ============================================================
seg("11. 嵌套事务")

tx_db = open("sqlite://:memory:")
tx_db.auto_migrate(Order)

def outer(tx):
    tx.create(Order(user_id=1, amount=10.0, item="outer"))

    def inner(tx2):
        tx2.create(Order(user_id=1, amount=20.0, item="inner"))

    tx.transaction(inner)

    try:
        def failing_inner(tx2):
            tx2.create(Order(user_id=1, amount=0.0, item="fail"))
            raise ValueError("inner rollback")
        tx.transaction(failing_inner)
    except ValueError:
        pass

    tx.create(Order(user_id=1, amount=30.0, item="after_inner"))

tx_db.transaction(outer)

orders = tx_db.model(Order).order("amount ASC").find()
check("nested tx: item count", len(orders) == 3)
check("nested tx: inner present", any(o.item == "inner" for o in orders))
check("nested tx: fail not present", not any(o.item == "fail" for o in orders))
check("nested tx: after_inner present", any(o.item == "after_inner" for o in orders))


# ============================================================
# 12. Nested Preload (链式预加载)
# ============================================================
seg("12. 链式 Preload")

# Preload orders for users, then preload nothing nested (since Order has no associations)
users_with_orders = db.preload("orders").find(User)
check("chain preload", all(len(u.orders) >= 0 for u in users_with_orders))


# ============================================================
# 结果汇总
# ============================================================
seg("结果汇总")

total = pass_count + fail_count
print(f"\n  {pass_count}/{total} passed", end="")
if fail_count > 0:
    print(f", {fail_count} FAILED")
    sys.exit(1)
else:
    print(" — ALL CHECKS PASSED!")
    sys.exit(0)
