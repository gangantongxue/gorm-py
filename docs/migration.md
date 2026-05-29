# AutoMigrate

> 示例代码: [examples/03_migration.py](../examples/03_migration.py)

AutoMigrate 自动维护数据库表结构，遵循 GORM 的安全迁移规则。

## 基本用法

```python
db.auto_migrate(User, Order, Product)  # 迁移一个或多个 Model
```

## 迁移行为

| 场景 | 行为 |
|------|------|
| 表不存在 | 创建表 |
| 表存在，Model 有新字段 | ALTER TABLE ADD COLUMN |
| 表存在，字段类型变化 | **忽略** (不修改已有列) |
| 表存在，Model 删除了字段 | **忽略** (不删除已有列) |
| 索引不存在 | CREATE INDEX |
| many_to_many 关联 | 自动创建 junction 表 |

## 手动建表/删表

```python
db.create_table(User)      # 仅创建表，不检查是否存在
db.drop_table(User)        # 删除表
db.has_table(User)         # 检查表是否存在 (True/False)
```

## 幂等性

AutoMigrate 可以安全地重复执行，不会重复创建已存在的表或列：

```python
db.auto_migrate(User)
db.auto_migrate(User)  # 第二次执行，无操作
```

## 自动索引

```python
class User(Model):
    name: str = Field(size=255, index=True)    # 创建普通索引
    email: str = Field(size=255, unique=True)  # 创建唯一索引
```

## Config

```python
from gorm import Config

db = open("sqlite:///app.db", Config(
    auto_migrate=True,  # 打开连接时自动迁移
))
```
