# 事务

> 示例代码: [examples/05_transactions.py](../examples/05_transactions.py)

## 闭包式事务 (推荐)

```python
def do_work(tx):
    tx.create(User(name="alice"))
    tx.create(User(name="bob"))

db.transaction(do_work)
# 成功: 自动 commit
# 异常: 自动 rollback
```

## 手动事务

```python
tx = db.begin()
try:
    tx.create(User(name="alice"))
    tx.commit()
except Exception:
    tx.rollback()
```

## 嵌套事务 (Savepoint)

```python
def outer(tx):
    tx.create(User(name="outer"))

    def inner(tx2):
        tx2.create(User(name="inner"))
        raise RuntimeError("inner fails")

    try:
        tx.transaction(inner)  # 内层自动 rollback
    except RuntimeError:
        pass  # 内层回滚不影响外层

    tx.create(User(name="after_inner"))

db.transaction(outer)
# 结果: outer 和 after_inner 被保存, inner 被回滚
```

## 事务隔离

未提交的事务中的变更对外部不可见：

```python
tx = db.begin()
tx.create(User(name="tx_only"))

# 外部查询看不到 tx_only
users = db.find(User)  # []

tx.commit()
# 提交后可见
users = db.find(User)  # [User(tx_only)]
```
