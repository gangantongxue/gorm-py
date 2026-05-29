# gorm-py

[中文](README.md) | [English](README.en.md)

Python 版 GORM —— 链式 API、自动迁移、关联预加载、钩子函数。像写 Go GORM 一样操作数据库。

## 特性

- **链式查询 API** — 与 Go GORM 一致的链式调用风格
- **零依赖** — SQLite 使用 Python 标准库 `sqlite3`，无需额外安装
- **自动迁移** — AutoMigrate 自动建表、添加缺失列、创建索引
- **Lambda 表达式** — `db.where(User.age > 18)` 运算符重载
- **关联 & 预加载** — BelongsTo / HasOne / HasMany / ManyToMany + Preload
- **生命周期钩子** — before_create / after_create / before_save / after_find 等 8 种钩子
- **软删除** — GormModel 内置软删除，unscoped() 查询已删除记录
- **事务 & 嵌套事务** — transaction() 闭包式事务，自动提交/回滚，支持 savepoint
- **Scopes** — 可复用的查询函数
- **SQL 日志** — 记录 SQL 语句、执行耗时和影响行数
- **多数据库** — SQLite(已实现) / PostgreSQL(需psycopg2) / MySQL(需pymysql)

## 快速开始

### 安装

```bash
pip install gorm-py
```

### 使用

```python
from gorm import open, Model, Field

class User(Model):
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255, index=True)
    age: int = Field(default=18)

db = open("sqlite://:memory:")  # 或 "sqlite:///app.db"
db.auto_migrate(User)

# Create
db.create(User(name="jinzhu", age=30))
db.create(User(name="bob", age=25))

# Read
user = db.where("name = ?", "jinzhu").first(User)
users = db.where("age > ?", 18).order("id DESC").limit(10).find(User)

# Lambda 表达式 (更 Pythonic)
users = db.where(User.age > 18).find(User)

# Update
db.model(User).where("id = ?", 1).update(name="jinzhu_new")

# Delete
db.delete(user)

# 事务
db.transaction(lambda tx: (
    tx.create(User(name="alice")),
    tx.create(User(name="bob")),
))
```

## 功能概览

### Model 定义

```python
from gorm import Model, GormModel, Field

class User(Model):
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255, index=True, unique=True)
    age: int = Field(default=18)
    email: str = Field(size=255, nullable=True)

class Product(GormModel):  # 自带 id, created_at, updated_at, deleted_at
    title: str = Field(size=255)
    price: float = Field()
```

### 链式查询

```python
users = (
    db.model(User)
    .where("age > ?", 18)
    .where("status = ?", "active")
    .order("id DESC")
    .limit(10)
    .offset(20)
    .find()
)

# 或 Lambda 表达式
users = db.where((User.age > 18) & (User.status == "active")).find(User)

# 支持的运算符: > < >= <= == != like in_ between IS NULL AND OR
users = db.where(User.name.like("%jin%")).find(User)
users = db.where(User.id.in_([1, 2, 3])).find(User)
users = db.where(User.age.between(18, 65)).find(User)
```

### 关联 (Associations)

```python
class Company(Model):
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)

class User(Model):
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)
    company_id: int = Field(nullable=True)
    company: Company = Field(belongs_to=Company)
    orders: list[Order] = Field(has_many="Order")

# 手动加载关联
company = db.model(user).association("company").find()
orders = db.model(user).association("orders").find()

# 预加载 (eager loading)
users = db.preload("company").preload("orders").find(User)
# users[0].company -> Company 实例
# users[0].orders -> [Order, ...]
```

### 软删除

```python
class User(GormModel):  # GormModel 自带 deleted_at 字段 (soft_delete)
    name: str = Field(size=255)

db.delete(user)  # 变为 UPDATE SET deleted_at = NOW()
users = db.find(User)  # 自动过滤 WHERE deleted_at IS NULL
users = db.model(User).unscoped().find()  # 查看包含已删除的全部记录
```

### ManyToMany

```python
class Student(Model):
    name: str = Field(size=255)
    courses: list[Course] = Field(many_to_many="Course")

class Course(Model):
    title: str = Field(size=255)

db.auto_migrate(Student, Course)  # 自动创建 junction 表
```

## 文档

| 模块 | 文档 | 示例 |
|------|------|------|
| Model 定义 | [docs/models.md](docs/models.md) | [examples/01_models.py](examples/01_models.py) |
| CRUD 操作 | [docs/crud.md](docs/crud.md) | [examples/02_crud.py](examples/02_crud.py) |
| AutoMigrate | [docs/migration.md](docs/migration.md) | [examples/03_migration.py](examples/03_migration.py) |
| 生命周期钩子 | [docs/hooks.md](docs/hooks.md) | [examples/04_hooks.py](examples/04_hooks.py) |
| 事务 | [docs/transactions.md](docs/transactions.md) | [examples/05_transactions.py](examples/05_transactions.py) |
| 链式查询 | [docs/query-builder.md](docs/query-builder.md) | [examples/06_query_builder.py](examples/06_query_builder.py) |
| Lambda 表达式 | [docs/lambda-expressions.md](docs/lambda-expressions.md) | [examples/07_lambda_where.py](examples/07_lambda_where.py) |
| Scopes | [docs/scopes.md](docs/scopes.md) | [examples/08_scopes.py](examples/08_scopes.py) |
| 软删除 | [docs/soft-delete.md](docs/soft-delete.md) | [examples/09_soft_delete.py](examples/09_soft_delete.py) |
| 关联 & 预加载 | [docs/associations.md](docs/associations.md) | [examples/10_associations.py](examples/10_associations.py) |
| ManyToMany | [docs/associations.md](docs/associations.md) | [examples/11_many_to_many.py](examples/11_many_to_many.py) |
| SQL 日志 | [docs/logger.md](docs/logger.md) | [examples/12_logger.py](examples/12_logger.py) |

完整演示: [examples/demo.py](examples/demo.py) — 一次性运行 50 项功能检查。

## 数据库支持

| 数据库 | DSN 格式 | 驱动 |
|--------|---------|------|
| SQLite | `sqlite:///path/to/db` 或 `sqlite://:memory:` | 标准库 sqlite3 |
| PostgreSQL | `postgres://user:pass@host:port/dbname` | `pip install psycopg2-binary` |
| MySQL | `mysql://user:pass@host:port/dbname` | `pip install pymysql` |

## API 参考

### DB 链式方法

| 方法 | 说明 |
|------|------|
| `.model(cls)` | 指定操作的目标 Model |
| `.where(cond, *args)` | AND 条件 (字符串或 Lambda 表达式) |
| `.or_where(cond, *args)` | OR 条件 |
| `.not_(cond, *args)` | NOT 条件 |
| `.order(col)` | 排序 |
| `.limit(n)` | 限制行数 |
| `.offset(n)` | 偏移 |
| `.select(*fields)` | 指定查询列 |
| `.group(col)` | 分组 |
| `.having(cond, *args)` | HAVING |
| `.join(table, on)` | JOIN |
| `.distinct()` | 去重 |
| `.preload(relation)` | 预加载关联 |
| `.scopes(*funcs)` | 应用 scope |
| `.unscoped()` | 跳过软删除过滤 |

### DB 终端方法

| 方法 | 说明 |
|------|------|
| `.create(instance)` | 插入 |
| `.find(model)` | 查询列表 |
| `.first(model)` | 查询第一条 (或 None) |
| `.last(model)` | 查询最后一条 |
| `.take(model)` | 随机一条 |
| `.save(instance)` | Upsert (INSERT 或 UPDATE) |
| `.update(**cols)` | 批量更新 |
| `.delete(instance?)` | 删除 |
| `.count(model)` | 计数 |
| `.exists(model)` | 存在性检查 |
| `.begin()` | 开启事务 |
| `.commit()` | 提交事务 |
| `.rollback()` | 回滚事务 |
| `.transaction(fn)` | 事务闭包 |
| `.raw(sql, *args)` | 原生 SQL |
| `.association(name)` | 获取关联操作对象 |
| `.auto_migrate(*models)` | 自动迁移 |

### Field 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `primary_key` | bool | 主键 |
| `auto_increment` | bool | 自增 |
| `default` | any | 默认值 |
| `unique` | bool | 唯一约束 |
| `index` | bool | 创建索引 |
| `nullable` | bool | 允许 NULL |
| `size` | int | 列长度 (VARCHAR) |
| `auto_now` | bool | 每次保存时更新 |
| `auto_now_add` | bool | 创建时设置 |
| `comment` | str | 注释 |
| `soft_delete` | bool | 标记为软删除字段 |
| `belongs_to` | str/class | BelongsTo 关联 |
| `has_one` | str | HasOne 关联 |
| `has_many` | str | HasMany 关联 |
| `many_to_many` | str | ManyToMany 关联 |
| `foreign_key` | str | 自定义外键列名 |

## 许可证

MIT License
