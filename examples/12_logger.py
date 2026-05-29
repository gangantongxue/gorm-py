#!/usr/bin/env python3
from __future__ import annotations
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gorm import open, Model, Field, Config
from gorm.logger import Logger

class User(Model):
    __tablename__ = "users"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)

logs = []
def capture(msg):
    logs.append(msg)

db = open(
    "sqlite://:memory:",
    Config(logger=Logger(writer=capture)),
)
db.auto_migrate(User)

print("=== Logger 示例 ===\n")

db.create(User(name="jinzhu"))
db.where(User.name == "jinzhu").first(User)

print(f"捕获到 {len(logs)} 条 SQL 日志:\n")
for i, log in enumerate(logs, 1):
    print(f"  {i}. {log}")

print(f"\n格式: [耗时] [rows:行数] SQL语句")
print("示例通过!")
