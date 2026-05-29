from __future__ import annotations
from typing import Any
from .field import Field, FieldMeta

_gorm_model_registry: dict[str, type] = {}


class ModelMeta(type):
    """Metaclass that collects Field declarations into __gorm_fields__."""

    def __new__(mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> type:
        cls = super().__new__(mcs, name, bases, namespace)

        gorm_fields: dict[str, FieldMeta] = {}

        for base in reversed(cls.__mro__):
            if hasattr(base, "__gorm_fields__"):
                gorm_fields.update(base.__gorm_fields__)
            for attr_name, attr_value in base.__dict__.items():
                if isinstance(attr_value, Field):
                    python_type = _resolve_annotation(base, attr_name)
                    gorm_fields[attr_name] = attr_value._meta(
                        column_name=attr_name,
                        python_type=python_type,
                    )

        cls.__gorm_fields__ = gorm_fields
        _gorm_model_registry[name] = cls

        return cls


def _resolve_annotation(cls: type, attr_name: str) -> type:
    import typing
    import re

    # Try get_type_hints for simple annotations
    try:
        hints = typing.get_type_hints(cls, include_extras=False)
        if attr_name in hints:
            return hints[attr_name]
    except Exception:
        pass

    # Fallback: parse the raw string annotation (Python 3.9 with __future__)
    ann = cls.__annotations__.get(attr_name, "") if hasattr(cls, "__annotations__") else ""
    if ann and isinstance(ann, str):
        ann = re.sub(r"Optional\[(\w+)\]", r"\1", ann)
        ann = ann.split("|")[0].strip()
        type_map = {"int": int, "str": str, "float": float, "bool": bool, "bytes": bytes}
        if ann in type_map:
            return type_map[ann]
    elif ann and not isinstance(ann, str):
        # Non-string annotation (already resolved), return as-is if it's a type
        if isinstance(ann, type):
            return ann

    return str


class Model(metaclass=ModelMeta):
    """Base class for all gorm models."""

    __tablename__: str = ""
    __gorm_fields__: dict[str, FieldMeta] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not cls.__tablename__:
            cls.__tablename__ = _camel_to_snake(cls.__name__)

    def __init__(self, **kwargs: Any) -> None:
        for field_name, field_meta in self.__gorm_fields__.items():
            if field_name in kwargs:
                setattr(self, field_name, kwargs[field_name])
            elif field_meta.default is not None:
                setattr(self, field_name, field_meta.default)

    @classmethod
    def primary_key_field(cls) -> FieldMeta | None:
        for meta in cls.__gorm_fields__.values():
            if meta.primary_key:
                return meta
        return None

    @classmethod
    def get_field(cls, name: str) -> FieldMeta | None:
        return cls.__gorm_fields__.get(name)

    @classmethod
    def soft_delete_field(cls) -> FieldMeta | None:
        """Return the soft-delete FieldMeta, or None if not configured."""
        for meta in cls.__gorm_fields__.values():
            if meta.soft_delete:
                return meta
        return None


def _camel_to_snake(name: str) -> str:
    import re

    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.lower()


def resolve_model(name_or_class: str | type) -> type | None:
    """Resolve a model reference (string or class) to a concrete Model class."""
    if isinstance(name_or_class, type):
        return name_or_class
    return _gorm_model_registry.get(name_or_class)


class GormModel(Model):
    """Convenience base model with common fields.

    Usage:
        class User(GormModel):
            name: str = Field(size=255)

    Provides: id, created_at, updated_at, deleted_at (soft delete).
    """

    id: int = Field(primary_key=True, auto_increment=True)
    created_at: str = Field(auto_now_add=True)
    updated_at: str = Field(auto_now=True)
    deleted_at: str | None = Field(soft_delete=True, nullable=True)
