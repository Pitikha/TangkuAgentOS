from __future__ import annotations

import logging
from logging import Logger as PyLogger
from typing import Any, Mapping

from .base import CoreComponent
from .constants import DEFAULT_LOG_FORMAT, LogLevel
from .exceptions import LoggerError


class _StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "metadata"):
            record.metadata = {}
        record.message = record.getMessage()
        formatted = super().format(record)
        if record.metadata:
            formatted = f"{formatted} | metadata={record.metadata}"
        return formatted


class Logger(CoreComponent):
    """Core kernel logger abstraction."""

    def __init__(self, name: str, level: LogLevel = LogLevel.INFO) -> None:
        self._name = name
        self._level = level
        self._initialized = False
        self._logger = logging.getLogger(name)
        self._configure_logger()

    @property
    def name(self) -> str:
        return self._name

    def _configure_logger(self) -> None:
        self._logger.handlers.clear()
        self._logger.propagate = False
        handler = logging.StreamHandler()
        formatter = _StructuredFormatter(DEFAULT_LOG_FORMAT)
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(self._level)

    def initialize(self) -> None:
        self._initialized = True
        self._logger.debug("Logger initialized.")

    def shutdown(self) -> None:
        self._logger.debug("Logger shutdown.")
        for handler in list(self._logger.handlers):
            handler.close()
            self._logger.removeHandler(handler)
        self._initialized = False

    def status(self) -> Mapping[str, Any]:
        return {
            "name": self._name,
            "level": self._level.name,
            "initialized": self._initialized,
            "handler_count": len(self._logger.handlers),
        }

    def metrics(self) -> Mapping[str, Any]:
        return {
            "handler_count": len(self._logger.handlers),
            "initialized": self._initialized,
        }

    def is_healthy(self) -> bool:
        return self._initialized and bool(self._logger.handlers)

    def set_level(self, level: LogLevel) -> None:
        self._level = level
        self._logger.setLevel(level)

    def log(self, level: LogLevel, message: str, **metadata: Any) -> None:
        if not message:
            raise LoggerError("Log message must be provided.")
        try:
            self._logger.log(level, message, extra={"metadata": metadata})
        except Exception as error:
            raise LoggerError(str(error)) from error

    def debug(self, message: str, **metadata: Any) -> None:
        self.log(LogLevel.DEBUG, message, **metadata)

    def info(self, message: str, **metadata: Any) -> None:
        self.log(LogLevel.INFO, message, **metadata)

    def warning(self, message: str, **metadata: Any) -> None:
        self.log(LogLevel.WARNING, message, **metadata)

    def error(self, message: str, **metadata: Any) -> None:
        self.log(LogLevel.ERROR, message, **metadata)

    def critical(self, message: str, **metadata: Any) -> None:
        self.log(LogLevel.CRITICAL, message, **metadata)
