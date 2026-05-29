# SQL 日志

> 示例代码: [examples/12_logger.py](../examples/12_logger.py)

gorm-py 支持输出 SQL 语句的执行日志，包含耗时和影响行数。

## 基本用法

```python
from gorm import open, Config, Model, Field
from gorm.logger import Logger

# 自定义日志输出函数
logs = []
def capture(msg):
    logs.append(msg)

db = open(
    "sqlite://:memory:",
    Config(logger=Logger(writer=capture)),
)

# 所有 SQL 执行都会被记录
db.create(User(name="jinzhu"))
db.find(User)
```

## 使用 Python logging

```python
import logging
from gorm import open, Config

db = open(
    "sqlite://:memory:",
    Config(log_level=logging.INFO),
)
# 日志通过 Python logging 模块输出到 stderr
```

## 日志格式

```
[0.45ms] [rows:1] INSERT INTO "users" ("name") VALUES (?)
[0.12ms] [rows:5] SELECT * FROM "users"
```

- `[耗时]` — 执行时间，单位毫秒
- `[rows:N]` — 影响的行数 (SELECT 返回行数，INSERT 为 1，UPDATE/DELETE 为受影响行数)
- `SQL语句` — 带占位符的原始 SQL
