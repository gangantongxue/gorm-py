import pytest
from gorm.model import Model, GormModel, ModelMeta
from gorm.field import Field, FieldMeta


class TestModelDefinition:
    def test_model_collects_fields(self):
        class User(Model):
            __tablename__ = "users"
            id: int = Field(primary_key=True)
            name: str = Field(size=255)

        assert hasattr(User, "__gorm_fields__")
        assert "id" in User.__gorm_fields__
        assert "name" in User.__gorm_fields__

        id_meta = User.__gorm_fields__["id"]
        assert id_meta.column_name == "id"
        assert id_meta.primary_key is True
        assert id_meta.python_type is int

        name_meta = User.__gorm_fields__["name"]
        assert name_meta.column_name == "name"
        assert name_meta.size == 255
        assert name_meta.python_type is str

    def test_model_table_name_default(self):
        class Product(Model):
            id: int = Field(primary_key=True)

        assert Product.__tablename__ == "product"

    def test_model_table_name_explicit(self):
        class OrderItem(Model):
            __tablename__ = "order_items"
            id: int = Field(primary_key=True)

        assert OrderItem.__tablename__ == "order_items"

    def test_model_primary_key_field(self):
        class User(Model):
            id: int = Field(primary_key=True)
            name: str = Field(size=255)

        pk = User.primary_key_field()
        assert pk is not None
        assert pk.column_name == "id"


class TestModelInstance:
    def test_create_instance_with_fields(self):
        class User(Model):
            id: int = Field(primary_key=True)
            name: str = Field(size=255)

        u = User(id=1, name="jinzhu")
        assert u.id == 1
        assert u.name == "jinzhu"

    def test_instance_field_default(self):
        class User(Model):
            id: int = Field(primary_key=True)
            age: int = Field(default=18)

        u = User(id=1)
        assert u.age == 18

    def test_instance_stores_values_in_dict(self):
        class User(Model):
            id: int = Field(primary_key=True)
            name: str = Field(size=255)

        u = User(id=1, name="jinzhu")
        assert "id" in u.__dict__
        assert u.__dict__["id"] == 1

    def test_inheritance_collects_parent_fields(self):
        class Base(Model):
            __tablename__ = "base"
            id: int = Field(primary_key=True)
            created_at: str = Field()

        class Child(Base):
            name: str = Field(size=255)

        assert "id" in Child.__gorm_fields__
        assert "created_at" in Child.__gorm_fields__
        assert "name" in Child.__gorm_fields__

    def test_non_field_annotations_ignored(self):
        class User(Model):
            id: int = Field(primary_key=True)
            temp: int = 0  # plain class var, not a Field

        assert "id" in User.__gorm_fields__
        assert "temp" not in User.__gorm_fields__


class TestGormModel:
    def test_gorm_model_has_base_fields(self):
        class User(GormModel):
            __tablename__ = "users"
            name: str = Field(size=255)

        assert "id" in User.__gorm_fields__
        assert "created_at" in User.__gorm_fields__
        assert "updated_at" in User.__gorm_fields__
        assert "deleted_at" in User.__gorm_fields__
        assert "name" in User.__gorm_fields__

    def test_gorm_model_primary_key(self):
        class User(GormModel):
            __tablename__ = "users"
            name: str = Field(size=255)

        pk = User.primary_key_field()
        assert pk is not None
        assert pk.column_name == "id"
        assert pk.auto_increment is True

    def test_gorm_model_soft_delete(self):
        class User(GormModel):
            __tablename__ = "users"
            name: str = Field(size=255)

        sd = User.soft_delete_field()
        assert sd is not None
        assert sd.column_name == "deleted_at"
        assert sd.soft_delete is True
