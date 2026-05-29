# Model 定义

> 示例代码: [examples/01_models.py](../examples/01_models.py)

gorm-py 使用 Python dataclass 风格的类定义来声明数据库表结构。

## 基础用法

```python
from gorm import Model, Field

class User(Model):
    __tablename__ = "users"  # 可选，默认自动从类名生成 (User -> user)
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255, index=True)
    age: int = Field(default=18)
    email: str = Field(size=255, unique=True, nullable=True)
```

## Field 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `primary_key` | bool | False | 主键 |
| `auto_increment` | bool | False | 自增 (仅整数类型) |
| `default` | any | None | 默认值 |
| `unique` | bool | False | 唯一约束 |
| `index` | bool | False | 创建索引 |
| `nullable` | bool | False | 允许 NULL |
| `size` | int | 0 | VARCHAR 长度 (0=VARCHAR 时使用 TEXT) |
| `auto_now` | bool | False | 每次保存时自动设置为当前时间 |
| `auto_now_add` | bool | False | 创建时自动设置为当前时间 |
| `comment` | str | "" | 列注释 |

## 支持的数据类型

| Python 类型 | SQLite 类型 | PostgreSQL | MySQL |
|-------------|-------------|------------|-------|
| `int` | INTEGER | INTEGER/SERIAL | INT |
| `str` (size>0) | VARCHAR(n) | VARCHAR(n) | VARCHAR(n) |
| `str` (size=0) | TEXT | TEXT | TEXT |
| `float` | REAL | DOUBLE PRECISION | DOUBLE |
| `bool` | INTEGER | BOOLEAN | TINYINT(1) |
| `bytes` | BLOB | BYTEA | BLOB |

## 表名自动推断

如果不设置 `__tablename__`，gorm-py 会自动将 CamelCase 类名转换为 snake_case 表名：

```python
class UserProfile(Model):
    pass  # __tablename__ = "user_profile"

class OrderItem(Model):
    pass  # __tablename__ = "order_item"
```

## 类方法

```python
# 获取主键字段
pk = User.primary_key_field()
print(pk.column_name)  # "id"

# 按名称获取字段
field = User.get_field("name")
print(field.python_type)  # <class 'str'>
```

## GormModel

`GormModel` 是 `Model` 的子类，自动包含常用字段：

```python
from gorm import GormModel, Field

class Product(GormModel):
    __tablename__ = "products"
    title: str = Field(size=255)

# 自动继承的字段:
#   id: int          — 主键, 自增
#   created_at: str  — 创建时间 (auto_now_add)
#   updated_at: str  — 更新时间 (auto_now)
#   deleted_at: str  — 软删除时间 (nullable, soft_delete)
```

## 继承

子类会自动继承父类的所有字段：

```python
class BaseModel(Model):
    id: int = Field(primary_key=True, auto_increment=True)
    created_at: str = Field(auto_now_add=True)

class User(BaseModel):
    name: str = Field(size=255)
    # 自动拥有 id 和 created_at 字段
```
