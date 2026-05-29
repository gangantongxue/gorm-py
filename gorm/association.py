from __future__ import annotations
from typing import Any
from .model import Model, resolve_model


class Association:
    """Performs CRUD operations on model relationships.

    Usage:
        db.model(user).association("orders").find()
        db.model(user).association("company").find()
    """

    def __init__(self, db, owner: Model, field_name: str) -> None:
        self._db = db
        self._owner = owner
        self._field_name = field_name
        owner_cls = type(owner)
        self._meta = owner_cls.__gorm_fields__[field_name]

    def find(self) -> Any:
        """Load the associated record(s)."""
        target_cls = self._resolve_target()
        if target_cls is None:
            return None

        if self._meta.belongs_to:
            return self._find_belongs_to(target_cls)
        elif self._meta.has_many:
            return self._find_has_many(target_cls)
        elif self._meta.has_one:
            return self._find_has_one(target_cls)
        elif self._meta.many_to_many:
            return self._find_many_to_many(target_cls)
        return None

    def _find_belongs_to(self, target_cls: type) -> Any:
        """SELECT * FROM target WHERE pk = owner.fk_value"""
        fk_col = self._meta.foreign_key or f"{self._field_name}_id"
        fk_val = getattr(self._owner, fk_col, None)
        if fk_val is None:
            return None
        pk = target_cls.primary_key_field()
        if pk is None:
            return None
        return self._db.where(f"{pk.column_name} = ?", fk_val).first(target_cls)

    def _find_has_many(self, target_cls: type) -> list[Model]:
        """SELECT * FROM target WHERE fk = owner.pk_value"""
        owner_cls = type(self._owner)
        owner_pk = owner_cls.primary_key_field()
        if owner_pk is None:
            return []
        owner_pk_val = getattr(self._owner, owner_pk.column_name)
        fk_col = self._meta.foreign_key or _infer_fk(owner_cls)
        return self._db.where(f"{fk_col} = ?", owner_pk_val).find(target_cls)

    def _find_has_one(self, target_cls: type) -> Model | None:
        """SELECT * FROM target WHERE fk = owner.pk_value LIMIT 1"""
        result = self._find_has_many(target_cls)
        return result[0] if result else None

    def _find_many_to_many(self, target_cls: type) -> list[Model]:
        """SELECT target.* FROM target JOIN junction ON target.pk = junction.target_fk
        WHERE junction.owner_fk = owner.pk_value"""
        owner_cls = type(self._owner)
        owner_pk = owner_cls.primary_key_field()
        if owner_pk is None:
            return []
        owner_pk_val = getattr(self._owner, owner_pk.column_name)

        jt, owner_fk, target_fk = _resolve_junction(owner_cls, target_cls, self._meta)
        target_pk = target_cls.primary_key_field()
        if target_pk is None:
            return []

        sql = (
            f'SELECT {jt}.{target_fk} FROM {jt} WHERE {jt}.{owner_fk} = ?'
        )
        rows = self._db.raw(sql, owner_pk_val)
        target_ids = [row[target_fk] for row in rows]
        if not target_ids:
            return []

        placeholders = ", ".join("?" for _ in target_ids)
        return self._db.where(
            f"{target_pk.column_name} IN ({placeholders})", *target_ids
        ).find(target_cls)

    def _resolve_target(self) -> type | None:
        """Resolve the target model class from the association metadata."""
        ref = self._meta.belongs_to or self._meta.has_many or self._meta.has_one or self._meta.many_to_many
        if ref is None:
            return None
        return resolve_model(ref)


def _infer_fk(owner_cls: type) -> str:
    """Infer the foreign key column name for a has_many/has_one relationship.

    e.g., User -> user_id, Company -> company_id
    """
    return f"{owner_cls.__name__.lower()}_id"


def _resolve_junction(owner_cls: type, target_cls: type, field_meta) -> tuple[str, str, str]:
    """Resolve junction table name and FK columns for many_to_many.

    Returns: (join_table_name, owner_fk_column, target_fk_column)
    """
    jt = field_meta.join_table
    if jt is None:
        tables = sorted([owner_cls.__tablename__, target_cls.__tablename__])
        jt = f"{tables[0]}_{tables[1]}"
    owner_fk = field_meta.join_foreign_key or f"{owner_cls.__name__.lower()}_id"
    target_fk = field_meta.join_references or f"{target_cls.__name__.lower()}_id"
    return jt, owner_fk, target_fk


def preload_relation(db, instances: list[Model], relation: str, model_cls: type) -> None:
    """Eager-load a relation onto a list of model instances.

    Args:
        db: The DB instance for queries.
        instances: List of model instances to populate.
        relation: The field name of the association.
        model_cls: The owner model class.
    """
    field_meta = model_cls.__gorm_fields__.get(relation)
    if field_meta is None:
        return

    target_cls = resolve_model(
        field_meta.belongs_to or field_meta.has_many or field_meta.has_one or field_meta.many_to_many
    )
    if target_cls is None:
        return

    if field_meta.has_many:
        _preload_has_many(db, instances, model_cls, field_meta, target_cls, relation)
    elif field_meta.has_one:
        _preload_has_one(db, instances, model_cls, field_meta, target_cls, relation)
    elif field_meta.belongs_to:
        _preload_belongs_to(db, instances, model_cls, field_meta, target_cls, relation)
    elif field_meta.many_to_many:
        _preload_many_to_many(db, instances, model_cls, field_meta, target_cls, relation)


def _preload_has_many(db, instances, owner_cls, field_meta, target_cls, relation):
    """Load has_many: collect owner PKs, query target WHERE fk IN (...), assign."""
    owner_pk = owner_cls.primary_key_field()
    if owner_pk is None:
        return
    owner_ids = {
        getattr(inst, owner_pk.column_name): inst
        for inst in instances
        if getattr(inst, owner_pk.column_name) is not None
    }
    if not owner_ids:
        return

    fk_col = field_meta.foreign_key or _infer_fk(owner_cls)
    placeholders = ", ".join("?" for _ in owner_ids)
    targets = db.where(f"{fk_col} IN ({placeholders})", *owner_ids.keys()).find(target_cls)

    # Assign: group by FK
    owner_map: dict[Any, list[Model]] = {k: [] for k in owner_ids}
    target_pk = target_cls.primary_key_field()
    for t in targets:
        fk_val = getattr(t, fk_col, None)
        if fk_val in owner_map:
            owner_map[fk_val].append(t)

    for owner_id, owner_inst in owner_ids.items():
        setattr(owner_inst, relation, owner_map.get(owner_id, []))


def _preload_has_one(db, instances, owner_cls, field_meta, target_cls, relation):
    """Load has_one: same as has_many but assign single record."""
    # Reuse has_many preload logic, then take first
    _preload_has_many(db, instances, owner_cls, field_meta, target_cls, relation)
    for inst in instances:
        items = getattr(inst, relation, [])
        setattr(inst, relation, items[0] if items else None)


def _preload_belongs_to(db, instances, owner_cls, field_meta, target_cls, relation):
    """Load belongs_to: collect FK values, query target WHERE pk IN (...), assign."""
    fk_col = field_meta.foreign_key or f"{relation}_id"
    fk_values: dict[Any, list[Any]] = {}
    for inst in instances:
        fk_val = getattr(inst, fk_col, None)
        if fk_val is not None:
            fk_values.setdefault(fk_val, []).append(inst)

    if not fk_values:
        return

    target_pk = target_cls.primary_key_field()
    if target_pk is None:
        return

    placeholders = ", ".join("?" for _ in fk_values)
    targets = db.where(f"{target_pk.column_name} IN ({placeholders})", *fk_values.keys()).find(target_cls)

    target_map: dict[Any, Model] = {}
    for t in targets:
        pk_val = getattr(t, target_pk.column_name)
        target_map[pk_val] = t

    for fk_val, owner_insts in fk_values.items():
        target = target_map.get(fk_val)
        for inst in owner_insts:
            setattr(inst, relation, target)


def _preload_many_to_many(db, instances, owner_cls, field_meta, target_cls, relation):
    """Preload many_to_many: query junction table, collect target IDs, load targets."""
    owner_pk = owner_cls.primary_key_field()
    if owner_pk is None:
        return
    owner_ids = [
        getattr(inst, owner_pk.column_name)
        for inst in instances
        if getattr(inst, owner_pk.column_name) is not None
    ]
    if not owner_ids:
        return

    jt, owner_fk, target_fk = _resolve_junction(owner_cls, target_cls, field_meta)
    target_pk = target_cls.primary_key_field()
    if target_pk is None:
        return

    # Query junction table for all owner IDs
    placeholders = ", ".join("?" for _ in owner_ids)
    jt_rows = db.raw(
        f"SELECT {jt}.{owner_fk}, {jt}.{target_fk} FROM {jt} WHERE {jt}.{owner_fk} IN ({placeholders})",
        *owner_ids,
    )

    # Collect target IDs
    target_ids = list({row[target_fk] for row in jt_rows})
    if not target_ids:
        for inst in instances:
            setattr(inst, relation, [])
        return

    # Load targets
    tp_placeholders = ", ".join("?" for _ in target_ids)
    targets = db.where(
        f"{target_pk.column_name} IN ({tp_placeholders})", *target_ids
    ).find(target_cls)

    target_map = {}
    for t in targets:
        target_map[getattr(t, target_pk.column_name)] = t

    # Build owner -> [targets] mapping
    owner_targets: dict[Any, list[Model]] = {oid: [] for oid in owner_ids}
    for row in jt_rows:
        oid = row[owner_fk]
        tid = row[target_fk]
        if oid in owner_targets and tid in target_map:
            owner_targets[oid].append(target_map[tid])

    for inst in instances:
        oid = getattr(inst, owner_pk.column_name)
        setattr(inst, relation, owner_targets.get(oid, []))
