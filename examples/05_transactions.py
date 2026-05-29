#!/usr/bin/env python3
from __future__ import annotations
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gorm import open, Model, Field

class Order(Model):
    __tablename__ = "orders"
    id: int = Field(primary_key=True, auto_increment=True)
    item: str = Field(size=255)
    amount: float = Field()

db = open("sqlite://:memory:")
db.auto_migrate(Order)
print("=== 事务示例 ===\n")

# 事务提交
def create_orders(tx):
    tx.create(Order(item="Apple", amount=10.0))
    tx.create(Order(item="Banana", amount=20.0))

db.transaction(create_orders)
print(f"transaction commit: {db.model(Order).count()} orders")

# 事务回滚
def create_and_fail(tx):
    tx.create(Order(item="RollbackMe", amount=99.0))
    raise ValueError("simulated error")

try:
    db.transaction(create_and_fail)
except ValueError:
    pass

print(f"transaction rollback (should be 2): {db.model(Order).count()} orders")

# 嵌套事务 (savepoint)
def outer(tx):
    tx.create(Order(item="Outer", amount=10.0))

    def inner(tx2):
        tx2.create(Order(item="Inner", amount=20.0))
    tx.transaction(inner)

    # 内层回滚不影响外层
    try:
        def failing_inner(tx2):
            tx2.create(Order(item="Fail", amount=0.0))
            raise RuntimeError("inner fail")
        tx.transaction(failing_inner)
    except RuntimeError:
        pass

    tx.create(Order(item="AfterInner", amount=30.0))

# 重新连接测试嵌套事务
db2 = open("sqlite://:memory:")
db2.auto_migrate(Order)
db2.transaction(outer)

all_items = [o.item for o in db2.model(Order).order("amount ASC").find()]
print(f"nested tx items: {all_items}")

print("\n事务通过!")
