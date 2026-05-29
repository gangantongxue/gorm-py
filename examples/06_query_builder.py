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
db.create(User(name="bob",   age=25, status="inactive"))
db.create(User(name="eve",   age=30, status="active"))
db.create(User(name="mallory", age=35, status="banned"))
db.create(User(name="trent", age=35, status="active"))

print("=== 链式查询示例 ===\n")

# 基础 where
users = db.model(User).where("age > ?", 20).find()
print(f"where age>20:     {[u.name for u in users]}")

# 多重 where (AND)
users = db.model(User).where("age > ?", 20).where("status = ?", "active").find()
print(f"where AND:         {[u.name for u in users]}")

# OR 条件
users = db.model(User).where("age < ?", 25).or_where("age > ?", 30).find()
print(f"or_where:          {[u.name for u in users]}")

# NOT 条件
users = db.model(User).where("age > ?", 20).not_("status = ?", "banned").find()
print(f"NOT condition:     {[u.name for u in users]}")

# ORDER BY + LIMIT + OFFSET
users = db.model(User).order("age DESC").limit(3).offset(1).find()
print(f"order+limit+offset:{[u.name for u in users]}")

# SELECT 指定列
u = db.model(User).select("name", "status").where("name = ?", "bob").first()
print(f"select columns:   name={u.name}, status={u.status}, age={u.age}(default)")

# GROUP BY + HAVING
rows = db.model(User).select("status", "COUNT(*) as cnt").group("status").find()
print(f"group by:          {[(r.status, r.age) for r in rows]}")

# COUNT
print(f"count all:         {db.model(User).count()}")

# JOIN
class Profile(Model):
    __tablename__ = "profiles"
    id: int = Field(primary_key=True, auto_increment=True)
    user_id: int = Field()
    bio: str = Field(size=500)

db.auto_migrate(Profile)
db.create(Profile(user_id=1, bio="Alice's bio"))
db.create(Profile(user_id=2, bio="Bob's bio"))

users = db.model(User).join("profiles", 'profiles.user_id = users.id').find()
print(f"join:              {[u.name for u in users]}")

print("\n链式查询通过!")
