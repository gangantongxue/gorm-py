#!/usr/bin/env python3
from __future__ import annotations
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gorm import open, Model, Field

class V1User(Model):
    __tablename__ = "users"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255, index=True)

db = open("sqlite://:memory:")
print("=== AutoMigrate 示例 ===\n")

# 首次迁移: 创建表
db.auto_migrate(V1User)
print(f"has_table: {db.has_table(V1User)}")

# 检查列
rows = db.raw("PRAGMA table_info('users')")
print(f"columns: {[r['name'] for r in rows]}")

# 模拟 Model 变更: 添加新字段
class V2User(Model):
    __tablename__ = "users"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255, index=True)
    age: int = Field(default=18)
    email: str = Field(size=255, unique=True)

db.auto_migrate(V2User)
rows = db.raw("PRAGMA table_info('users')")
print(f"after add columns: {[r['name'] for r in rows]}")

# 检查索引
idxs = db.raw("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='users'")
print(f"indexes: {[r['name'] for r in idxs]}")

# 幂等性: 重复执行不报错
db.auto_migrate(V2User)
print("idempotent: OK")

# 删除表
db.drop_table(V2User)
print(f"after drop: has_table={db.has_table(V2User)}")

print("\nAutoMigrate 通过!")
