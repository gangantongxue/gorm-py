#!/usr/bin/env python3
from __future__ import annotations
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gorm import open, Model, Field

class User(Model):
    __tablename__ = "users"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)
    age: int = Field(default=18)
    status: str = Field(size=50, default="active")

db = open("sqlite://:memory:")
db.auto_migrate(User)

db.create(User(name="alice", age=22, status="active"))
db.create(User(name="bob",   age=35, status="active"))
db.create(User(name="eve",   age=28, status="inactive"))

print("=== Scopes 示例 ===\n")

# 定义 scope: 活跃用户
def active_users(db):
    return db.where("status = ?", "active")

# 定义 scope: 成年人
def adults(db):
    return db.where("age >= ?", 18)

# 带参数的 scope (闭包)
def paginate(page, page_size):
    def scope(db):
        return db.offset((page - 1) * page_size).limit(page_size)
    return scope

# 使用单个 scope
users = db.scopes(active_users).model(User).find()
print(f"active_users:        {[u.name for u in users]}")

# 多个 scope 组合
users = db.scopes(active_users, adults).model(User).find()
print(f"active + adults:     {[u.name for u in users]}")

# scope 带参数
users = db.scopes(paginate(1, 2)).model(User).order("age ASC").find()
print(f"paginate page1 size2:{[u.name for u in users]}")

users = db.scopes(paginate(2, 2)).model(User).order("age ASC").find()
print(f"paginate page2 size2:{[u.name for u in users]}")

# scope 结合 count
cnt = db.scopes(active_users).model(User).count()
print(f"active users count:  {cnt}")

print("\nScopes 通过!")
