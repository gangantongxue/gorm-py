from __future__ import annotations
from typing import Any

HOOK_BEFORE_CREATE = "before_create"
HOOK_AFTER_CREATE = "after_create"
HOOK_BEFORE_SAVE = "before_save"
HOOK_AFTER_SAVE = "after_save"
HOOK_BEFORE_UPDATE = "before_update"
HOOK_AFTER_UPDATE = "after_update"
HOOK_BEFORE_DELETE = "before_delete"
HOOK_AFTER_DELETE = "after_delete"
HOOK_AFTER_FIND = "after_find"


def call_hook(instance: Any, hook_name: str) -> Any:
    """Call a hook method on an instance if it exists and is callable.

    Returns the instance (or None if hook raised).
    Raises if hook explicitly raises.
    """
    fn = getattr(instance, hook_name, None)
    if callable(fn):
        return fn()
    return instance


def call_find_hooks(instances: list[Any]) -> list[Any]:
    """Call after_find on each result instance."""
    for instance in instances:
        call_hook(instance, HOOK_AFTER_FIND)
    return instances
