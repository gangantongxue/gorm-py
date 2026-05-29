# Scopes

> 示例代码: [examples/08_scopes.py](../examples/08_scopes.py)

Scope 是接受 DB 实例并返回 DB 实例的函数，用于封装可复用的查询逻辑。

## 基本用法

```python
def active_users(db):
    return db.where("status = ?", "active")

users = db.scopes(active_users).model(User).find()
```

## 多个 Scope 组合

```python
def active(db):
    return db.where("status = ?", "active")

def adults(db):
    return db.where("age >= ?", 18)

users = db.scopes(active, adults).model(User).find()
# 等价于: db.where("status = ?", "active").where("age >= ?", 18)
```

## 带参数的 Scope

```python
def paginate(page, page_size):
    def scope(db):
        return db.offset((page - 1) * page_size).limit(page_size)
    return scope

users = db.scopes(paginate(1, 20)).model(User).find()

# 组合使用
users = db.scopes(active_users, paginate(2, 10)).model(User).find()
```
