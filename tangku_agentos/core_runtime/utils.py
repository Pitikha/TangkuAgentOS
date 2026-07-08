from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Mapping


_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class SingletonMeta(type):
    """A lightweight singleton metaclass for core runtime classes."""

    _instances: dict[type, object] = {}

    def __call__(cls, *args: object, **kwargs: object) -> object:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def validate_identifier(value: str) -> bool:
    """Validate a core identifier string."""
    return bool(_IDENTIFIER_PATTERN.match(value))


def merge_configurations(*configurations: Mapping[str, Any]) -> dict[str, Any]:
    """Merge multiple configuration dictionaries into one."""
    merged: dict[str, Any] = {}
    for conf in configurations:
        merged.update(conf)
    return merged
