#!/usr/bin/env python3
from __future__ import annotations
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gorm import open, Model, Field

class HookUser(Model):
    __tablename__ = "users"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)

    calls: list[str] = []

    def before_save(self):    HookUser.calls.append("before_save")
    def after_save(self):     HookUser.calls.append("after_save")
    def before_create(self):  HookUser.calls.append("before_create")
    def after_create(self):   HookUser.calls.append("after_create")
    def before_update(self):  HookUser.calls.append("before_update")
    def after_update(self):   HookUser.calls.append("after_update")
    def before_delete(self):  HookUser.calls.append("before_delete")
    def after_delete(self):   HookUser.calls.append("after_delete")
    def after_find(self):     HookUser.calls.append("after_find")

db = open("sqlite://:memory:")
db.auto_migrate(HookUser)
print("=== 生命周期钩子 (Hooks) 示例 ===\n")

# Create hooks
HookUser.calls = []
u = db.create(HookUser(name="jinzhu"))
print(f"create hooks: {HookUser.calls}")
# before_save -> before_create -> [INSERT] -> after_create -> after_save

# Update hooks
HookUser.calls = []
u.name = "updated"
db.save(u)
print(f"update hooks: {HookUser.calls}")
# before_save -> before_update -> [UPDATE] -> after_update -> after_save

# Delete hooks
HookUser.calls = []
db.delete(u)
print(f"delete hooks: {HookUser.calls}")
# before_delete -> [DELETE] -> after_delete

# after_find hook
HookUser.calls = []
db.create(HookUser(name="alice"))
HookUser.calls = []
db.find(HookUser)
print(f"after_find called: {'after_find' in HookUser.calls}")

# Modify fields in hooks
class TrimUser(Model):
    __tablename__ = "trim_users"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)
    def before_create(self):
        self.name = self.name.strip().upper()

db.auto_migrate(TrimUser)
u = db.create(TrimUser(name="  hello world  "))
print(f"before_create modifies: name='{u.name}'")

print("\nHooks 通过!")
