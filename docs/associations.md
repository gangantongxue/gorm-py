# 关联 & 预加载

> 示例代码: [examples/10_associations.py](../examples/10_associations.py) | [examples/11_many_to_many.py](../examples/11_many_to_many.py)

## 关联类型

| 类型 | Field 参数 | 外键位置 |
|------|-----------|---------|
| BelongsTo | `Field(belongs_to=Company)` | 当前 Model (如 `company_id`) |
| HasOne | `Field(has_one="CreditCard")` | 对方 Model |
| HasMany | `Field(has_many="Order")` | 对方 Model |
| ManyToMany | `Field(many_to_many="Language")` | Junction 表 |

## BelongsTo

```python
class User(Model):
    company_id: int = Field(nullable=True)
    company: Company = Field(belongs_to=Company)

# 加载关联
company = db.model(user).association("company").find()
# SQL: SELECT * FROM companies WHERE id = user.company_id
```

## HasMany

```python
class User(Model):
    orders: list[Order] = Field(has_many="Order")
# Order 表需要有 user_id 列

# 加载关联
orders = db.model(user).association("orders").find()
# SQL: SELECT * FROM orders WHERE user_id = user.id
```

## ManyToMany

```python
class Student(Model):
    courses: list[Course] = Field(many_to_many="Course")

class Course(Model):
    title: str = Field(size=255)

db.auto_migrate(Student, Course)  # 自动创建 courses_students junction 表
```

## 自定义外键

```python
class User(Model):
    company: Company = Field(
        belongs_to=Company,
        foreign_key="corp_id"  # 自定义外键列名
    )
    orders: list[Order] = Field(
        has_many="Order",
        foreign_key="buyer_id"
    )
```

## 自定义 Junction 表

```python
class User(Model):
    roles: list[Role] = Field(
        many_to_many="Role",
        join_table="user_role_map",         # 自定义 junction 表名
        join_foreign_key="uid",              # junction 表中指向 User 的 FK
        join_references="rid",               # junction 表中指向 Role 的 FK
    )
```

## Preload (预加载)

预加载在查询主记录后一次性加载关联数据，避免 N+1 查询问题。

```python
# 预加载单个关联
users = db.preload("company").find(User)
# users[0].company -> Company 实例

# 链式预加载多个关联
users = db.preload("company").preload("orders").find(User)
# users[0].company -> Company 实例
# users[0].orders -> [Order, ...]
```
