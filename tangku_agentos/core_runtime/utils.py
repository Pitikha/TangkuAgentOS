from __future__ import annotations

import re
import uuid
from typing import Any, Callable, Dict, List, Mapping, Optional, Type, Union

from .exceptions import ConfigurationError, SchemaValidationError
from .types import ConfigData, ConfigKey, ConfigValue, ConfigurationSchema


_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class SingletonMeta(type):
    """
    Thread-safe singleton metaclass for core runtime classes.
    Ensures only one instance is created per class.
    """

    _instances: Dict[Type, Any] = {}
    _lock = type("SingletonLock", (), {"acquire": lambda self: None, "release": lambda self: None})()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def validate_identifier(value: str) -> bool:
    """Validate a core identifier string (alphanumeric + underscore, no leading digits)."""
    return bool(_IDENTIFIER_PATTERN.match(value))


def merge_configurations(*configurations: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple configuration dictionaries into one.
    Later configurations override earlier ones.
    """
    merged: Dict[str, Any] = {}
    for conf in configurations:
        merged.update(conf)
    return merged


def deep_merge_configurations(*configurations: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Deep merge multiple configuration dictionaries into one.
    Nested dictionaries are merged recursively.
    """
    merged: Dict[str, Any] = {}
    for conf in configurations:
        for key, value in conf.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = deep_merge_configurations(merged[key], value)
            else:
                merged[key] = value
    return merged


def validate_schema(
    config: ConfigData,
    schema: ConfigurationSchema,
) -> None:
    """
    Validate a configuration against a schema.
    Raises SchemaValidationError if validation fails.
    """
    if schema.validators:
        invalid_keys: List[str] = []
        for key, value in config.items():
            validator = schema.validators.get(key)
            if validator and not validator(value):
                invalid_keys.append(key)
        if invalid_keys:
            raise SchemaValidationError(
                f"Invalid values for configuration keys: {', '.join(invalid_keys)}"
            )

    if schema.required_keys:
        missing_keys = [key for key in schema.required_keys if key not in config]
        if missing_keys:
            raise ConfigurationError(
                f"Missing required configuration keys: {', '.join(missing_keys)}"
            )

    if schema.nested_schemas:
        for key, nested_schema in schema.nested_schemas.items():
            if key in config:
                nested_config = config[key]
                if not isinstance(nested_config, dict):
                    raise SchemaValidationError(
                        f"Nested configuration for '{key}' must be a dictionary."
                    )
                validate_schema(nested_config, nested_schema)


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for logging/tracing."""
    return str(uuid.uuid4())


def generate_request_id() -> str:
    """Generate a unique request ID for logging/tracing."""
    return str(uuid.uuid4())


def coerce_config_value(value: Any) -> ConfigValue:
    """
    Coerce a value into a valid ConfigValue type.
    Converts non-serializable types (e.g., sets, tuples) into lists or dicts.
    """
    if isinstance(value, (list, tuple)):
        return [coerce_config_value(v) for v in value]
    elif isinstance(value, dict):
        return {str(k): coerce_config_value(v) for k, v in value.items()}
    elif isinstance(value, (str, int, float, bool, type(None))):
        return value
    else:
        return str(value)


def filter_config_by_prefix(
    config: ConfigData,
    prefix: str,
) -> ConfigData:
    """Filter a configuration dictionary to only include keys with the given prefix."""
    return {k: v for k, v in config.items() if k.startswith(prefix)}


def flatten_config(
    config: ConfigData,
    parent_key: str = "",
    sep: str = ".",
) -> ConfigData:
    """
    Flatten a nested configuration dictionary.
    Example: {"a": {"b": 1}} -> {"a.b": 1}
    """
    items: ConfigData = {}
    for k, v in config.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_config(v, new_key, sep))
        else:
            items[new_key] = v
    return items


def expand_config(
    config: ConfigData,
    sep: str = ".",
) -> ConfigData:
    """
    Expand a flattened configuration dictionary.
    Example: {"a.b": 1} -> {"a": {"b": 1}}
    """
    expanded: ConfigData = {}
    for k, v in config.items():
        keys = k.split(sep)
        current = expanded
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = v
    return expanded
