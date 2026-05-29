#!/usr/bin/env python3
from __future__ import annotations
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gorm import open, Model, Field

class Student(Model):
    __tablename__ = "students"
    id: int = Field(primary_key=True, auto_increment=True)
    name: str = Field(size=255)
    courses: list[Course] = Field(many_to_many="Course")

class Course(Model):
    __tablename__ = "courses"
    id: int = Field(primary_key=True, auto_increment=True)
    title: str = Field(size=255)

db = open("sqlite://:memory:")
db.auto_migrate(Student, Course)

print("=== ManyToMany 示例 ===\n")

# 准备数据
s1 = db.create(Student(name="alice"))
s2 = db.create(Student(name="bob"))

math = db.create(Course(title="Math"))
cs   = db.create(Course(title="Computer Science"))
eng  = db.create(Course(title="English"))

# 插入关联: alice -> [Math, CS], bob -> [English]
# 自动生成的 junction 表: courses_students
db.raw("INSERT INTO courses_students (student_id, course_id) VALUES (?, ?)", s1.id, math.id)
db.raw("INSERT INTO courses_students (student_id, course_id) VALUES (?, ?)", s1.id, cs.id)
db.raw("INSERT INTO courses_students (student_id, course_id) VALUES (?, ?)", s2.id, eng.id)

# --- 手动加载 ---
print("--- 手动加载 (association) ---")
courses = db.model(s1).association("courses").find()
print(f"alice.courses: {[c.title for c in courses]}")

courses = db.model(s2).association("courses").find()
print(f"bob.courses:   {[c.title for c in courses]}")

# --- 预加载 ---
print("\n--- 预加载 (preload) ---")
students = db.preload("courses").find(Student)
for s in students:
    cs_list = [c.title for c in s.courses]
    print(f"  {s.name}: {cs_list}")

print("\nManyToMany 通过!")
