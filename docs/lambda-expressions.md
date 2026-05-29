# Lambda 表达式 where

> 示例代码: [examples/07_lambda_where.py](../examples/07_lambda_where.py)

除了字符串占位符，gorm-py 支持通过运算符重载实现更 Pythonic 的查询条件。

## 比较运算符

```python
# 基础比较
db.where(User.age > 18).find(User)      # >  (大于)
db.where(User.age >= 18).find(User)     # >= (大于等于)
db.where(User.age < 65).find(User)      # <  (小于)
db.where(User.age <= 65).find(User)     # <= (小于等于)
db.where(User.name == "jinzhu").first(User)  # == (等于)
db.where(User.name != "bob").find(User)      # != (不等于)
```

## NULL 判断

```python
db.where(User.email == None).find(User)  # IS NULL
db.where(User.email != None).find(User)  # IS NOT NULL
```

## 高级运算符

```python
# LIKE
db.where(User.name.like("%jin%")).find(User)

# IN
db.where(User.id.in_([1, 2, 3])).find(User)

# BETWEEN
db.where(User.age.between(18, 65)).find(User)
```

## 组合表达式

```python
# AND
db.where((User.age > 18) & (User.status == "active")).find(User)

# OR
db.where((User.name == "alice") | (User.name == "eve")).find(User)
```

## 混合模式

Lambda 表达式和字符串模式可以混合使用：

```python
db.where(User.age > 18).where("status = ?", "active").find(User)
```

## 运算符对照表

| 运算符 | SQL | 示例 |
|--------|-----|------|
| `==` | `=` | `User.name == "jinzhu"` |
| `!=` | `!=` | `User.name != "bob"` |
| `>` | `>` | `User.age > 18` |
| `>=` | `>=` | `User.age >= 18` |
| `<` | `<` | `User.age < 65` |
| `<=` | `<=` | `User.age <= 65` |
| `== None` | `IS NULL` | `User.email == None` |
| `!= None` | `IS NOT NULL` | `User.email != None` |
| `.like()` | `LIKE` | `User.name.like("%jin%")` |
| `.in_()` | `IN (?)` | `User.id.in_([1, 2, 3])` |
| `.between()` | `BETWEEN` | `User.age.between(18, 65)` |
| `&` | `AND` | `(a==1) & (b==2)` |
| `\|` | `OR` | `(a==1) \| (b==2)` |
