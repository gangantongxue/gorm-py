#!/usr/bin/env python3
from __future__ import annotations
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gorm import Model, GormModel, Field

class User(Model):
    __tablename__ = "users"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255, index=True)
    age: int = Field(default=18)
    email: str = Field(size=255, unique=True, nullable=True)

class Product(GormModel):
    __tablename__ = "products"
    title: str = Field(size=255)
    price: float = Field()

class Company(Model):
    __tablename__ = "companies"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)
    users: list[User] = Field(has_many="User")

class UserWithCompany(Model):
    __tablename__ = "users_c"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)
    company_id: int = Field(nullable=True)
    company: Company = Field(belongs_to=Company)

print("=== Model 定义示例 ===\n")

print(f"User 字段: {list(User.__gorm_fields__.keys())}")
print(f"User 主键: {User.primary_key_field().column_name}")
print(f"User 表名: {User.__tablename__}")
print()

print(f"Product (GormModel) 字段: {list(Product.__gorm_fields__.keys())}")
print(f"  自动继承: id, created_at, updated_at, deleted_at")
print(f"  自定义: title, price")
print()

print(f"UserWithCompany.company 关联: {UserWithCompany.__gorm_fields__['company'].belongs_to}")
print(f"Company.users 关联: {Company.__gorm_fields__['users'].has_many}")
print()

for name, meta in User.__gorm_fields__.items():
    flags = []
    if meta.primary_key: flags.append("PK")
    if meta.auto_increment: flags.append("AUTO_INCREMENT")
    if meta.unique: flags.append("UNIQUE")
    if meta.index: flags.append("INDEX")
    if meta.nullable: flags.append("NULLABLE")
    print(f"  {name}: {meta.python_type.__name__} {' '.join(flags)}")

print("\n所有示例通过!")
