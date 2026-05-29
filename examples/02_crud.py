#!/usr/bin/env python3
from __future__ import annotations
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gorm import open, Model, Field

class User(Model):
    __tablename__ = "users"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)
    age: int = Field(default=18)

db = open("sqlite://:memory:")
db.auto_migrate(User)
print("=== 基础 CRUD 示例 ===\n")

# Create
u = db.create(User(name="jinzhu", age=30))
print(f"create: id={u.id}, name={u.name}, age={u.age}")

db.create(User(name="bob", age=25))
db.create(User(name="alice", age=22))

# Read
all_users = db.find(User)
print(f"find all: {len(all_users)} users")

u = db.where("id = ?", 1).first(User)
print(f"first by id: {u.name}")

u = db.order("age DESC").first(User)
print(f"last (order DESC): {u.name}")

# Count
cnt = db.model(User).where("age > ?", 20).count()
print(f"count age>20: {cnt}")

# Exists
print(f"exists jinzhu: {db.model(User).where('name = ?', 'jinzhu').exists()}")
print(f"exists nobody: {db.model(User).where('name = ?', 'nobody').exists()}")

# Update
db.model(User).where("id = ?", 1).update(name="jinzhu_new", age=31)
u = db.where("id = ?", 1).first(User)
print(f"update: name={u.name}, age={u.age}")

# Save (upsert)
new_u = User(name="charlie")
db.save(new_u)
print(f"save insert: id={new_u.id}")

new_u.name = "charlie_updated"
db.save(new_u)
print(f"save update: {db.where('id = ?', new_u.id).first(User).name}")

# Delete
db.delete(new_u)
print(f"after delete, count: {db.model(User).count()}")

# Order & limit
users = db.model(User).order("age ASC").limit(2).find()
print(f"order+limit: {[u.name for u in users]}")

print("\n所有 CRUD 操作通过!")
