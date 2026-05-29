# gorm-py

[中文](README.md) | [English](README.en.md)

Python version of GORM — chained API, auto migration, association preloading, hooks. Operate databases just like Go GORM.

## Features

- **Chained Query API** — consistent chained calling style matching Go GORM
- **Zero Dependencies** — SQLite uses Python stdlib `sqlite3`, no extra installation required
- **Auto Migration** — AutoMigrate automatically creates tables, adds missing columns, and creates indexes
- **Lambda Expressions** — `db.where(User.age > 18)` via operator overloading
- **Associations & Preloading** — BelongsTo / HasOne / HasMany / ManyToMany + Preload
- **Lifecycle Hooks** — 8 hooks: before_create / after_create / before_save / after_find and more
- **Soft Delete** — GormModel includes built-in soft delete, unscoped() to query deleted records
- **Transactions & Nested Transactions** — transaction() closure-style, auto commit/rollback with savepoint support
- **Scopes** — reusable query functions
- **SQL Logging** — records SQL statements, execution time, and affected rows
- **Multi-Database** — SQLite (implemented) / PostgreSQL (requires psycopg2) / MySQL (requires pymysql)

## Quick Start

### Installation

```bash
pip install gorm-py
```

### Usage

```python
from gorm import open, Model, Field

class User(Model):
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255, index=True)
    age: int = Field(default=18)

db = open("sqlite://:memory:")  # or "sqlite:///app.db"
db.auto_migrate(User)

# Create
db.create(User(name="jinzhu", age=30))
db.create(User(name="bob", age=25))

# Read
user = db.where("name = ?", "jinzhu").first(User)
users = db.where("age > ?", 18).order("id DESC").limit(10).find(User)

# Lambda Expressions (more Pythonic)
users = db.where(User.age > 18).find(User)

# Update
db.model(User).where("id = ?", 1).update(name="jinzhu_new")

# Delete
db.delete(user)

# Transaction
db.transaction(lambda tx: (
    tx.create(User(name="alice")),
    tx.create(User(name="bob")),
))
```

## Feature Overview

### Model Definition

```python
from gorm import Model, GormModel, Field

class User(Model):
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255, index=True, unique=True)
    age: int = Field(default=18)
    email: str = Field(size=255, nullable=True)

class Product(GormModel):  # includes id, created_at, updated_at, deleted_at by default
    title: str = Field(size=255)
    price: float = Field()
```

### Chained Queries

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

# Or with Lambda Expressions
users = db.where((User.age > 18) & (User.status == "active")).find(User)

# Supported operators: > < >= <= == != like in_ between IS NULL AND OR
users = db.where(User.name.like("%jin%")).find(User)
users = db.where(User.id.in_([1, 2, 3])).find(User)
users = db.where(User.age.between(18, 65)).find(User)
```

### Associations

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

# Manually load associations
company = db.model(user).association("company").find()
orders = db.model(user).association("orders").find()

# Eager Loading
users = db.preload("company").preload("orders").find(User)
# users[0].company -> Company instance
# users[0].orders -> [Order, ...]
```

### Soft Delete

```python
class User(GormModel):  # GormModel includes deleted_at field (soft_delete)
    name: str = Field(size=255)

db.delete(user)  # becomes UPDATE SET deleted_at = NOW()
users = db.find(User)  # automatically filters WHERE deleted_at IS NULL
users = db.model(User).unscoped().find()  # view all records including deleted
```

### ManyToMany

```python
class Student(Model):
    name: str = Field(size=255)
    courses: list[Course] = Field(many_to_many="Course")

class Course(Model):
    title: str = Field(size=255)

db.auto_migrate(Student, Course)  # automatically creates junction table
```

## Documentation

| Module | Docs | Examples |
|--------|------|----------|
| Model Definition | [docs/models.md](docs/models.md) | [examples/01_models.py](examples/01_models.py) |
| CRUD Operations | [docs/crud.md](docs/crud.md) | [examples/02_crud.py](examples/02_crud.py) |
| AutoMigrate | [docs/migration.md](docs/migration.md) | [examples/03_migration.py](examples/03_migration.py) |
| Lifecycle Hooks | [docs/hooks.md](docs/hooks.md) | [examples/04_hooks.py](examples/04_hooks.py) |
| Transactions | [docs/transactions.md](docs/transactions.md) | [examples/05_transactions.py](examples/05_transactions.py) |
| Chained Queries | [docs/query-builder.md](docs/query-builder.md) | [examples/06_query_builder.py](examples/06_query_builder.py) |
| Lambda Expressions | [docs/lambda-expressions.md](docs/lambda-expressions.md) | [examples/07_lambda_where.py](examples/07_lambda_where.py) |
| Scopes | [docs/scopes.md](docs/scopes.md) | [examples/08_scopes.py](examples/08_scopes.py) |
| Soft Delete | [docs/soft-delete.md](docs/soft-delete.md) | [examples/09_soft_delete.py](examples/09_soft_delete.py) |
| Associations & Preloading | [docs/associations.md](docs/associations.md) | [examples/10_associations.py](examples/10_associations.py) |
| ManyToMany | [docs/associations.md](docs/associations.md) | [examples/11_many_to_many.py](examples/11_many_to_many.py) |
| SQL Logging | [docs/logger.md](docs/logger.md) | [examples/12_logger.py](examples/12_logger.py) |

Full demo: [examples/demo.py](examples/demo.py) — runs 50 feature checks in one go.

## Database Support

| Database | DSN Format | Driver |
|----------|-----------|--------|
| SQLite | `sqlite:///path/to/db` or `sqlite://:memory:` | stdlib sqlite3 |
| PostgreSQL | `postgres://user:pass@host:port/dbname` | `pip install psycopg2-binary` |
| MySQL | `mysql://user:pass@host:port/dbname` | `pip install pymysql` |

## API Reference

### DB Chain Methods

| Method | Description |
|--------|-------------|
| `.model(cls)` | Specify the target Model |
| `.where(cond, *args)` | AND condition (string or Lambda expression) |
| `.or_where(cond, *args)` | OR condition |
| `.not_(cond, *args)` | NOT condition |
| `.order(col)` | Order by |
| `.limit(n)` | Limit rows |
| `.offset(n)` | Offset |
| `.select(*fields)` | Specify query columns |
| `.group(col)` | Group by |
| `.having(cond, *args)` | HAVING |
| `.join(table, on)` | JOIN |
| `.distinct()` | Distinct |
| `.preload(relation)` | Preload associations |
| `.scopes(*funcs)` | Apply scopes |
| `.unscoped()` | Skip soft delete filter |

### DB Terminal Methods

| Method | Description |
|--------|-------------|
| `.create(instance)` | Insert |
| `.find(model)` | Query list |
| `.first(model)` | Query first (or None) |
| `.last(model)` | Query last |
| `.take(model)` | Query random one |
| `.save(instance)` | Upsert (INSERT or UPDATE) |
| `.update(**cols)` | Batch update |
| `.delete(instance?)` | Delete |
| `.count(model)` | Count |
| `.exists(model)` | Existence check |
| `.begin()` | Begin transaction |
| `.commit()` | Commit transaction |
| `.rollback()` | Rollback transaction |
| `.transaction(fn)` | Transaction closure |
| `.raw(sql, *args)` | Raw SQL |
| `.association(name)` | Get association operator |
| `.auto_migrate(*models)` | Auto migrate |

### Field Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `primary_key` | bool | Primary key |
| `auto_increment` | bool | Auto increment |
| `default` | any | Default value |
| `unique` | bool | Unique constraint |
| `index` | bool | Create index |
| `nullable` | bool | Allow NULL |
| `size` | int | Column length (VARCHAR) |
| `auto_now` | bool | Update on every save |
| `auto_now_add` | bool | Set on creation |
| `comment` | str | Comment |
| `soft_delete` | bool | Mark as soft delete field |
| `belongs_to` | str/class | BelongsTo association |
| `has_one` | str | HasOne association |
| `has_many` | str | HasMany association |
| `many_to_many` | str | ManyToMany association |
| `foreign_key` | str | Custom foreign key column name |

## License

MIT License
