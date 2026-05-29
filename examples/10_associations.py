#!/usr/bin/env python3
from __future__ import annotations
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gorm import open, Model, Field

class Company(Model):
    __tablename__ = "companies"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)

class Order(Model):
    __tablename__ = "orders"
    id: int = Field(primary_key=True, auto_increment=True)
    user_id: int = Field()
    item: str = Field(size=255)
    amount: float = Field()

class User(Model):
    __tablename__ = "users"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)
    company_id: int = Field(nullable=True)
    company: Company = Field(belongs_to=Company)
    orders: list[Order] = Field(has_many=Order)

db = open("sqlite://:memory:")
db.auto_migrate(Company, User, Order)

print("=== 关联 (Associations) 示例 ===\n")

# 准备数据
acme = db.create(Company(name="Acme Corp"))
globex = db.create(Company(name="Globex"))

db.create(User(name="alice", company_id=acme.id))
db.create(User(name="bob",   company_id=globex.id))
db.create(User(name="eve",   company_id=None))

# 用户订单
def create_orders(tx):
    tx.create(Order(user_id=1, item="Laptop",   amount=1200.0))
    tx.create(Order(user_id=1, item="Mouse",    amount=25.0))
    tx.create(Order(user_id=2, item="Keyboard", amount=80.0))
db.transaction(create_orders)

# --- BelongsTo ---
print("--- BelongsTo ---")
alice = db.where(User.name == "alice").first(User)
company = db.model(alice).association("company").find()
print(f"alice.company: {company.name if company else 'None'}")

eve = db.where(User.name == "eve").first(User)
company = db.model(eve).association("company").find()
print(f"eve.company:   {company.name if company else 'None'}")

# --- HasMany ---
print("\n--- HasMany ---")
alice = db.where(User.name == "alice").first(User)
orders = db.model(alice).association("orders").find()
print(f"alice.orders:  {[o.item for o in orders]}")

bob = db.where(User.name == "bob").first(User)
orders = db.model(bob).association("orders").find()
print(f"bob.orders:    {[o.item for o in orders]}")

# --- Preload (预加载) ---
print("\n--- Preload ---")
users = db.preload("company").preload("orders").find(User)
for u in users:
    c = u.company.name if u.company else "-"
    orders_list = [o.item for o in u.orders] if u.orders else []
    print(f"  {u.name}: company={c}, orders={orders_list}")

print("\n关联操作通过!")
