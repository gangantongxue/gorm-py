# 链式查询 (Query Builder)

> 示例代码: [examples/06_query_builder.py](../examples/06_query_builder.py)

DB 对象是不可变的 —— 每次链式方法调用返回一个新的 DB 副本。

## 条件方法

```python
# AND 条件
db.where("age > ?", 18).where("status = ?", "active")

# OR 条件
db.where("age < ?", 18).or_where("age > ?", 65)

# NOT 条件
db.where("age > ?", 18).not_("status = ?", "banned")
```

## 排序 & 分页

```python
db.model(User).order("id DESC").limit(10).offset(20)
```

## 字段选择

```python
# 只查询指定列
db.model(User).select("name", "email").find()

# 注意: 未选择的列使用 Field 默认值
```

## GROUP BY & HAVING

```python
db.model(Order).select("user_id", "SUM(amount) as total").group("user_id").find()
db.model(Order).select("user_id", "COUNT(*) as cnt").group("user_id").having("cnt > ?", 1).find()
```

## JOIN

```python
db.model(User).join("profiles", "profiles.user_id = users.id").find()
```

## DISTINCT

```python
db.model(User).select("status").distinct().find()
```

## 原生 SQL

```python
rows = db.raw("SELECT * FROM users WHERE age > ?", 18)
# 返回 list[dict[str, Any]]
```

## 完整链式方法清单

| 方法 | 说明 |
|------|------|
| `.model(cls)` | 指定 Model |
| `.table(name)` | 指定表名 |
| `.where(cond, *args)` | AND 条件 (多次调用=多个 AND) |
| `.or_where(cond, *args)` | OR 条件 |
| `.not_(cond, *args)` | NOT 条件 |
| `.order(col)` | 排序 |
| `.limit(n)` | LIMIT |
| `.offset(n)` | OFFSET |
| `.select(*fields)` | 指定 SELECT 列 |
| `.omit(*fields)` | 排除指定列 |
| `.group(col)` | GROUP BY |
| `.having(cond, *args)` | HAVING |
| `.join(table, on)` | JOIN |
| `.distinct()` | DISTINCT |
| `.preload(relation)` | 预加载关联 |
| `.scopes(*funcs)` | 应用 scope |
| `.unscoped()` | 跳过软删除过滤 |
