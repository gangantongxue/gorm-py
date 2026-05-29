# 软删除

> 示例代码: [examples/09_soft_delete.py](../examples/09_soft_delete.py)

软删除将 `DELETE` 操作替换为 `UPDATE SET deleted_at = NOW()`，记录被标记为已删除但数据保留在数据库中。

## 使用 GormModel

```python
from gorm import GormModel, Field

class User(GormModel):  # 自带 id, created_at, updated_at, deleted_at
    name: str = Field(size=255)
```

## 手动配置

```python
from gorm import Model, Field

class User(Model):
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)
    deleted_at: str = Field(soft_delete=True, nullable=True)
```

## 行为

- `db.delete(user)` → `UPDATE users SET deleted_at='2024-01-01...' WHERE id=?`
- `db.find(User)` → `SELECT * FROM users WHERE deleted_at IS NULL`
- `db.model(User).count()` → `SELECT COUNT(*) FROM users WHERE deleted_at IS NULL`
- `db.model(User).where("name = ?", "bob").first(User)` → 自动添加 `deleted_at IS NULL`

## Unscoped

```python
# 查询所有记录 (包括已删除)
deleted_users = db.model(User).unscoped().find()

# 查询特定已删除记录
user = db.model(User).unscoped().where("id = ?", 1).first(User)

# 计数 (包括已删除)
total = db.model(User).unscoped().count()
```
