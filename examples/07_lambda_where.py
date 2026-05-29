#!/usr/bin/env python3
from __future__ import annotations
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gorm import open, Model, Field

class User(Model):
    __tablename__ = "users"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)
    age: int = Field(default=18)
    email: str = Field(size=255, nullable=True)

db = open("sqlite://:memory:")
db.auto_migrate(User)

db.create(User(name="alice", age=22, email="alice@test.com"))
db.create(User(name="bob",   age=25, email=None))
db.create(User(name="eve",   age=30, email="eve@test.com"))

print("=== Lambda 表达式 where 示例 ===\n")

# 比较运算符
users = db.where(User.age > 20).find(User)
print(f"age > 20:      {[u.name for u in users]}")

users = db.where(User.age >= 25).find(User)
print(f"age >= 25:     {[u.name for u in users]}")

users = db.where(User.age < 25).find(User)
print(f"age < 25:      {[u.name for u in users]}")

users = db.where(User.age <= 22).find(User)
print(f"age <= 22:     {[u.name for u in users]}")

# == 和 !=
u = db.where(User.name == "bob").first(User)
print(f"name == 'bob':  {u.name if u else 'None'}")

users = db.where(User.name != "bob").find(User)
print(f"name != 'bob':  {[u.name for u in users]}")

# IS NULL / IS NOT NULL
users = db.where(User.email == None).find(User)
print(f"email IS NULL:  {[u.name for u in users]}")

users = db.where(User.email != None).find(User)
print(f"email NOT NULL: {[u.name for u in users]}")

# LIKE
users = db.where(User.name.like("%ob%")).find(User)
print(f"name LIKE '%ob%': {[u.name for u in users]}")

# IN
users = db.where(User.age.in_([22, 30])).find(User)
print(f"age IN [22,30]:   {[u.name for u in users]}")

# BETWEEN
users = db.where(User.age.between(22, 25)).find(User)
print(f"age BETWEEN 22..25: {[u.name for u in users]}")

# AND / OR 组合
users = db.where((User.age > 20) & (User.email != None)).find(User)
print(f"(age>20) & (email NOT NULL): {[u.name for u in users]}")

users = db.where((User.name == "alice") | (User.name == "eve")).find(User)
print(f"(name=='alice') | (name=='eve'): {[u.name for u in users]}")

# 混合 lambda + 字符串
users = db.where(User.age > 20).where("email IS NOT NULL").find(User)
print(f"lambda + string:  {[u.name for u in users]}")

# 统计
print(f"count age>=25:  {db.where(User.age >= 25).count(User)}")

print("\nLambda 表达式通过!")
