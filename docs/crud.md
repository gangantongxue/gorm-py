# CRUD 操作

> 示例代码: [examples/02_crud.py](../examples/02_crud.py)

gorm-py 提供了与 Go GORM 一致的 CRUD API。

## 连接数据库

```python
from gorm import open, Model, Field

db = open("sqlite://:memory:")  # 内存数据库
db = open("sqlite:///app.db")   # 文件数据库
```

## Create

```python
user = db.create(User(name="jinzhu", age=30))
print(user.id)  # 自动设置自增主键: 1
```

## Read

```python
# 查询所有
users = db.find(User)

# 条件查询
user = db.where("id = ?", 1).first(User)      # 第一条或 None
users = db.where("age > ?", 18).find(User)     # 列表

# 排序 & 分页
users = db.model(User).order("id DESC").limit(10).find(User)
users = db.model(User).order("id DESC").limit(10).offset(20).find(User)

# Last & Take
user = db.last(User)   # 最后一条 (按主键降序)
user = db.take(User)   # 随机一条
```

## Update

```python
# 批量更新
db.model(User).where("id = ?", 1).update(name="new_name", age=31)

# 单列更新 (跳过 hooks)
db.model(User).where("id = ?", 1).update_column("age", 32)
```

## Save (Upsert)

```python
# 新记录: 执行 INSERT
user = User(name="charlie", age=22)
db.save(user)  # user.id 被自动设置

# 已有记录: 执行 UPDATE
user.name = "charlie_updated"
db.save(user)
```

## Delete

```python
# 按实例删除
db.delete(user)

# 按条件批量删除
db.model(User).where("age < ?", 18).delete()
db.model(User).delete()  # 删除所有
```

## 辅助方法

```python
# 计数
count = db.model(User).where("age > ?", 18).count()

# 存在性检查
exists = db.model(User).where("name = ?", "jinzhu").exists()  # True/False
```
