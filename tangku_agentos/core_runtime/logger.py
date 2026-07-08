from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from logging import FileHandler, Handler, Logger as PyLogger, StreamHandler
from logging.handlers import RotatingFileHandler
from queue import Queue
from threading import RLock, Thread
from typing import Any, Callable, Dict, Mapping, Optional, Union

from .base import CoreComponent
from .constants import DEFAULT_LOG_FORMAT, JSON_LOG_FORMAT, LogFormat, LogLevel
from .exceptions import LogHandlerError, LogRotationError, LoggerError
from .types import CorrelationID, LogContext, Metadata, RequestID


class StructuredFormatter(logging.Formatter):
    """Formatter for structured logging (text or JSON)."""

    def __init__(self, fmt: Optional[str] = None, log_format: LogFormat = LogFormat.TEXT):
        super().__init__(fmt)
        self.log_format = log_format

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        if self.log_format == LogFormat.JSON:
            log_data = {
                "timestamp": self.formatTime(record),
                "name": record.name,
                "level": record.levelname,
                "message": record.message,
                "metadata": getattr(record, "metadata", {}),
            }
            if hasattr(record, "correlation_id"):
                log_data["correlation_id"] = record.correlation_id
            if hasattr(record, "request_id"):
                log_data["request_id"] = record.request_id
            return json.dumps(log_data)
        else:
            formatted = super().format(record)
            metadata = getattr(record, "metadata", {})
            if metadata:
                formatted = f"{formatted} | metadata={metadata}"
            if hasattr(record, "correlation_id"):
                formatted = f"{formatted} | correlation_id={record.correlation_id}"
            if hasattr(record, "request_id"):
                formatted = f"{formatted} | request_id={record.request_id}"
            return formatted


class AsyncHandler(Handler):
    """Asynchronous log handler using a queue and background thread."""

    def __init__(self, handler: Handler):
        super().__init__()
        self._handler = handler
        self._queue: Queue[logging.LogRecord] = Queue()
        self._thread: Optional[Thread] = None
        self._running = False
        self._lock = RLock()

    def start(self) -> None:
        """Start the background thread."""
        with self._lock:
            if self._thread is not None:
                return
            self._running = True
            self._thread = Thread(target=self._process_queue, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """Stop the background thread."""
        with self._lock:
            self._running = False
            if self._thread is not None:
                self._thread.join(timeout=1.0)
                self._thread = None

    def _process_queue(self) -> None:
        """Process log records from the queue."""
        while self._running:
            try:
                record = self._queue.get(timeout=0.1)
                self._handler.handle(record)
            except Exception:
                pass

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to the queue."""
        self._queue.put(record)

    def close(self) -> None:
        """Close the handler."""
        self.stop()
        self._handler.close()


class Logger(CoreComponent):
    """
    Production-grade logger with:
    - Structured JSON logging
    - File logging with rotation
    - Async logging
    - Correlation IDs and request IDs
    - Custom formatting
    """

    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        log_format: LogFormat = LogFormat.TEXT,
        file_path: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        async_logging: bool = False,
    ) -> None:
        self._name = name
        self._level = level
        self._log_format = log_format
        self._file_path = file_path
        self._max_bytes = max_bytes
        self._backup_count = backup_count
        self._async_logging = async_logging
        self._initialized = False
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        self._handlers: List[Handler] = []
        self._async_handlers: List[AsyncHandler] = []
        self._context: LogContext = LogContext()
        self._lock = RLock()
        self._configure_logger()

    @property
    def name(self) -> str:
        return self._name

    def _configure_logger(self) -> None:
        """Configure the logger with handlers."""
        self._logger.handlers.clear()
        self._logger.propagate = False

        formatter = StructuredFormatter(self._log_format)

        # Stream handler
        stream_handler = StreamHandler()
        stream_handler.setFormatter(formatter)
        self._logger.addHandler(stream_handler)
        self._handlers.append(stream_handler)

        # File handler with rotation
        if self._file_path:
            try:
                os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
                file_handler = RotatingFileHandler(
                    self._file_path,
                    maxBytes=self._max_bytes,
                    backupCount=self._backup_count,
                )
                file_handler.setFormatter(formatter)
                self._logger.addHandler(file_handler)
                self._handlers.append(file_handler)
            except Exception as e:
                raise LogRotationError(f"Failed to configure file logging: {e}") from e

        # Async handlers
        if self._async_logging:
            for handler in self._handlers:
                async_handler = AsyncHandler(handler)
                async_handler.start()
                self._async_handlers.append(async_handler)

        self._initialized = True

    def initialize(self) -> None:
        """Initialize the logger."""
        self._logger.debug("Logger initialized.")

    def shutdown(self) -> None:
        """Shutdown the logger."""
        self._logger.debug("Logger shutdown.")
        for handler in self._handlers:
            handler.close()
            self._logger.removeHandler(handler)
        for async_handler in self._async_handlers:
            async_handler.stop()
        self._handlers.clear()
        self._async_handlers.clear()
        self._initialized = False

    def status(self) -> Mapping[str, Any]:
        """Get the status of the logger."""
        return {
            "name": self._name,
            "level": self._level.name,
            "initialized": self._initialized,
            "handler_count": len(self._handlers),
            "async_logging": self._async_logging,
            "file_path": self._file_path,
        }

    def metrics(self) -> Mapping[str, Any]:
        """Get metrics for the logger."""
        return {
            "handler_count": len(self._handlers),
            "initialized": self._initialized,
            "async_logging": self._async_logging,
        }

    def is_healthy(self) -> bool:
        """Check if the logger is healthy."""
        return self._initialized and bool(self._handlers)

    def set_level(self, level: LogLevel) -> None:
        """Set the log level."""
        self._level = level
        self._logger.setLevel(level)

    def set_context(self, context: LogContext) -> None:
        """Set the log context (correlation_id, request_id, metadata)."""
        self._context = context

    def set_correlation_id(self, correlation_id: CorrelationID) -> None:
        """Set the correlation ID for all subsequent logs."""
        self._context.correlation_id = correlation_id

    def set_request_id(self, request_id: RequestID) -> None:
        """Set the request ID for all subsequent logs."""
        self._context.request_id = request_id

    def set_metadata(self, metadata: Metadata) -> None:
        """Set metadata for all subsequent logs."""
        self._context.metadata = metadata

    def _log(
        self,
        level: LogLevel,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Internal log method with context."""
        if not message:
            raise LoggerError("Log message must be provided.")

        metadata = {**self._context.metadata, **kwargs.get("metadata", {})}
        correlation_id = kwargs.get("correlation_id", self._context.correlation_id)
        request_id = kwargs.get("request_id", self._context.request_id)

        try:
            extra = {
                "metadata": metadata,
                "correlation_id": correlation_id,
                "request_id": request_id,
            }
            self._logger.log(level, message, extra=extra)
        except Exception as e:
            raise LoggerError(str(e)) from e

    def log(
        self,
        level: LogLevel,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Log a message with the given level and context."""
        self._log(level, message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        self._log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log a critical message."""
        self._log(LogLevel.CRITICAL, message, **kwargs)

    async def log_async(
        self,
        level: LogLevel,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Log a message asynchronously."""
        if not self._async_logging:
            self.log(level, message, **kwargs)
            return

        metadata = {**self._context.metadata, **kwargs.get("metadata", {})}
        correlation_id = kwargs.get("correlation_id", self._context.correlation_id)
        request_id = kwargs.get("request_id", self._context.request_id)

        try:
            extra = {
                "metadata": metadata,
                "correlation_id": correlation_id,
                "request_id": request_id,
            }
            record = self._logger.makeRecord(
                self._name,
                level,
                "",
                0,
                message,
                (),
                extra,
            )
            for async_handler in self._async_handlers:
                async_handler.emit(record)
        except Exception as e:
            raise LoggerError(str(e)) from e

    async def debug_async(self, message: str, **kwargs: Any) -> None:
        """Log a debug message asynchronously."""
        await self.log_async(LogLevel.DEBUG, message, **kwargs)

    async def info_async(self, message: str, **kwargs: Any) -> None:
        """Log an info message asynchronously."""
        await self.log_async(LogLevel.INFO, message, **kwargs)

    async def warning_async(self, message: str, **kwargs: Any) -> None:
        """Log a warning message asynchronously."""
        await self.log_async(LogLevel.WARNING, message, **kwargs)

    async def error_async(self, message: str, **kwargs: Any) -> None:
        """Log an error message asynchronously."""
        await self.log_async(LogLevel.ERROR, message, **kwargs)

    async def critical_async(self, message: str, **kwargs: Any) -> None:
        """Log a critical message asynchronously."""
        await self.log_async(LogLevel.CRITICAL, message, **kwargs)
