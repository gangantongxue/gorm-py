#!/usr/bin/env python3
from __future__ import annotations
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from gorm import open, GormModel, Field, Config

class User(GormModel):
    __tablename__ = "users"
    name: str = Field(size=255)

db = open(
    "sqlite://:memory:",
    Config(now_func=lambda: datetime(2024, 6, 1, 12, 0, 0).isoformat()),
)
db.auto_migrate(User)

print("=== Soft Delete 示例 ===\n")

db.create(User(name="alice"))
db.create(User(name="bob"))

# 软删除 bob
bob = db.where(User.name == "bob").first(User)
db.delete(bob)

# 默认查询自动过滤已删除
users = db.find(User)
print(f"正常查询 (排除已删除): {[u.name for u in users]}")

# unscoped 查看全部
all_users = db.model(User).unscoped().find()
print(f"unscoped (包含已删除):  {[u.name for u in all_users]}")

# 检查删除时间
deleted = db.model(User).unscoped().where(User.name == "bob").first(User)
print(f"bob 删除时间:            {deleted.deleted_at}")

# count 也受软删除影响
print(f"count (正常):           {db.model(User).count()}")
print(f"count (unscoped):       {db.model(User).unscoped().count()}")

# exists
print(f"exists bob (正常):      {db.where(User.name == 'bob').exists(User)}")
print(f"exists bob (unscoped):  {db.where(User.name == 'bob').unscoped().exists(User)}")

print("\nSoft Delete 通过!")
