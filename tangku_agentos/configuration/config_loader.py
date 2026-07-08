#!/usr/bin/env python3
"""
Configuration loader for TangkuAgentOS.

This module provides functionality to load configuration from YAML or JSON files,
with support for environment variable substitution.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml


class ConfigLoader:
    """
    Loads configuration from YAML or JSON files.
    Supports environment variable substitution using ${VAR_NAME} syntax.
    """

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize the ConfigLoader.

        Args:
            config_path: Path to the configuration file. If None, uses default paths.
        """
        self.config_path = Path(config_path) if config_path else None
        self._config: Dict[str, Any] = {}

    def load(self, path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Load configuration from a file.

        Args:
            path: Path to the configuration file. If None, uses the path provided in __init__.

        Returns:
            Dictionary containing the loaded configuration.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            ValueError: If the configuration file is invalid.
        """
        load_path = Path(path) if path else self.config_path
        if not load_path:
            # Try default paths
            default_paths = [
                Path("config.yaml"),
                Path("config.yml"),
                Path("config.json"),
                Path("tangku_agentos/config.yaml"),
            ]
            for p in default_paths:
                if p.exists():
                    load_path = p
                    break
            else:
                self._config = {}
                return self._config

        if not load_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {load_path}")

        # Load the file based on its extension
        suffix = load_path.suffix.lower()
        if suffix in (".yaml", ".yml"):
            self._load_yaml(load_path)
        elif suffix == ".json":
            self._load_json(load_path)
        else:
            raise ValueError(f"Unsupported configuration file format: {suffix}")

        # Substitute environment variables
        self._substitute_env_vars(self._config)

        return self._config

    def _load_yaml(self, path: Path) -> None:
        """Load configuration from a YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f) or {}

    def _load_json(self, path: Path) -> None:
        """Load configuration from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            self._config = json.load(f)

    def _substitute_env_vars(self, data: Any) -> None:
        """
        Recursively substitute environment variables in the configuration.
        Supports ${VAR_NAME} syntax.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    self._substitute_env_vars(value)
                elif isinstance(value, str):
                    data[key] = self._substitute_env_in_string(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    self._substitute_env_vars(item)
                elif isinstance(item, str):
                    data[i] = self._substitute_env_in_string(item)

    def _substitute_env_in_string(self, value: str) -> str:
        """Substitute environment variables in a string."""
        pattern = r"\$\{([^}]+)\}"

        def replace(match: re.Match[str]) -> str:
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))

        return re.sub(pattern, replace, value)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: Dot-separated key (e.g., "providers.openai.api_key").
            default: Default value if the key is not found.

        Returns:
            The configuration value, or the default if not found.
        """
        if not self._config:
            self.load()

        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def get_config(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary."""
        if not self._config:
            self.load()
        return self._config

    def reload(self) -> Dict[str, Any]:
        """Reload the configuration from disk."""
        self._config = {}
        return self.load()

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Dot-separated key (e.g., "providers.openai.api_key").
            value: Value to set.
        """
        if not self._config:
            self.load()

        keys = key.split(".")
        current = self._config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

    def save(self, path: Optional[Union[str, Path]] = None) -> None:
        """
        Save the configuration to a file.

        Args:
            path: Path to save the configuration. If None, uses the original path.
        """
        save_path = Path(path) if path else self.config_path
        if not save_path:
            raise ValueError("No path specified for saving configuration")

        suffix = save_path.suffix.lower()
        if suffix in (".yaml", ".yml"):
            with open(save_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config, f, default_flow_style=False)
        elif suffix == ".json":
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2)
        else:
            raise ValueError(f"Unsupported configuration file format: {suffix}")
