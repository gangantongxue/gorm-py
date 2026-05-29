# 生命周期钩子 (Hooks)

> 示例代码: [examples/04_hooks.py](../examples/04_hooks.py)

在 Model 上定义特定名称的方法，gorm-py 会在对应时机自动调用。

## 支持的钩子

| 方法名 | 触发时机 |
|--------|---------|
| `before_save` | Create 和 Update 之前 |
| `after_save` | Create 和 Update 之后 |
| `before_create` | Create 之前 |
| `after_create` | Create 之后 |
| `before_update` | Update 之前 |
| `after_update` | Update 之后 |
| `before_delete` | Delete 之前 |
| `after_delete` | Delete 之后 |
| `after_find` | 从数据库查询出来后 |

## 执行顺序

```
Create:  before_save → before_create → [INSERT] → after_create → after_save
Update:  before_save → before_update → [UPDATE] → after_update → after_save
Delete:  before_delete → [DELETE] → after_delete
Find:    [SELECT] → after_find
```

## 用法

```python
class User(Model):
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)

    def before_create(self):
        """在 INSERT 之前自动调用，可以修改字段值"""
        self.name = self.name.strip().upper()

    def after_create(self):
        """在 INSERT 之后自动调用"""
        print(f"User {self.id} created")
```

## 注意事项

- 钩子方法名必须完全匹配（区分大小写）
- 钩子方法接收 `self` 作为唯一参数
- `before_*` 钩子中可以修改实例的字段值
- `before_*` 钩子中抛出异常会阻止操作执行
- `after_find` 在每条查询结果上都会被调用
