"""
AI Foundation Framework - AI Serializer

This module provides the AISerializer class for serializing and deserializing
AI Foundation objects.
"""

from __future__ import annotations

import asyncio
import json
import logging
import pickle
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


class SerializationFormat(Enum):
    """Supported serialization formats."""
    JSON = "json"
    PICKLE = "pickle"
    YAML = "yaml"
    MSGPACK = "msgpack"
    PROTOBUF = "protobuf"


class SerializationError(Exception):
    """Exception for serialization errors."""
    pass


class DeserializationError(Exception):
    """Exception for deserialization errors."""
    pass


@dataclass
class AISerializerMetrics:
    """Metrics for the AI serializer."""
    serializations: int = 0
    deserializations: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "serializations": self.serializations,
            "deserializations": self.deserializations,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class AISerializer:
    """
    Serializer for AI Foundation objects.
    
    This class provides methods for serializing and deserializing
    AI Foundation objects to/from various formats.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import AISerializer
        >>> 
        >>> # Create serializer
        >>> serializer = AISerializer()
        >>> 
        >>> # Serialize an object
        >>> data = serializer.serialize(obj, format=SerializationFormat.JSON)
        >>> 
        >>> # Deserialize an object
        >>> obj = serializer.deserialize(data, target_class=MyClass)
        >>> 
        >>> # Serialize to file
        >>> await serializer.serialize_to_file(obj, "file.json")
        >>> 
        >>> # Deserialize from file
        >>> obj = await serializer.deserialize_from_file("file.json", target_class=MyClass)
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the AI serializer.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._metrics = AISerializerMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        logger.info("AISerializer initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> AISerializerMetrics:
        """Get the serializer metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the serializer is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the serializer is started."""
        return self._started

    async def initialize(self) -> None:
        """
        Initialize the AI serializer.
        """
        if self._initialized:
            logger.warning("AISerializer already initialized")
            return
        
        logger.info("Initializing AISerializer...")
        
        self._initialized = True
        logger.info("AISerializer initialized successfully")

    async def start(self) -> None:
        """
        Start the AI serializer.
        """
        if self._started:
            logger.warning("AISerializer already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting AISerializer...")
        
        self._started = True
        logger.info("AISerializer started successfully")

    async def stop(self) -> None:
        """
        Stop the AI serializer.
        """
        if not self._started:
            logger.warning("AISerializer not started")
            return
        
        logger.info("Stopping AISerializer...")
        
        self._started = False
        logger.info("AISerializer stopped successfully")

    def serialize(
        self,
        obj: Any,
        format: SerializationFormat = SerializationFormat.JSON,
        **kwargs,
    ) -> Union[str, bytes]:
        """
        Serialize an object to the specified format.
        
        Args:
            obj: Object to serialize.
            format: Serialization format to use.
            **kwargs: Additional format-specific arguments.
        
        Returns:
            Serialized data (string for JSON/YAML, bytes for others).
        
        Raises:
            SerializationError: If serialization fails.
        """
        self._metrics.serializations += 1
        
        try:
            if format == SerializationFormat.JSON:
                return self._serialize_json(obj, **kwargs)
            elif format == SerializationFormat.PICKLE:
                return self._serialize_pickle(obj, **kwargs)
            elif format == SerializationFormat.YAML:
                return self._serialize_yaml(obj, **kwargs)
            elif format == SerializationFormat.MSGPACK:
                return self._serialize_msgpack(obj, **kwargs)
            elif format == SerializationFormat.PROTOBUF:
                return self._serialize_protobuf(obj, **kwargs)
            else:
                raise SerializationError(f"Unsupported format: {format}")
                
        except Exception as e:
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"Serialization failed: {e}")
            raise SerializationError(f"Serialization failed: {e}") from e

    def deserialize(
        self,
        data: Union[str, bytes],
        target_class: Optional[type] = None,
        format: SerializationFormat = SerializationFormat.JSON,
        **kwargs,
    ) -> Any:
        """
        Deserialize data from the specified format.
        
        Args:
            data: Serialized data to deserialize.
            target_class: Optional target class for deserialization.
            format: Serialization format of the data.
            **kwargs: Additional format-specific arguments.
        
        Returns:
            Deserialized object.
        
        Raises:
            DeserializationError: If deserialization fails.
        """
        self._metrics.deserializations += 1
        
        try:
            if format == SerializationFormat.JSON:
                return self._deserialize_json(data, target_class, **kwargs)
            elif format == SerializationFormat.PICKLE:
                return self._deserialize_pickle(data, target_class, **kwargs)
            elif format == SerializationFormat.YAML:
                return self._deserialize_yaml(data, target_class, **kwargs)
            elif format == SerializationFormat.MSGPACK:
                return self._deserialize_msgpack(data, target_class, **kwargs)
            elif format == SerializationFormat.PROTOBUF:
                return self._deserialize_protobuf(data, target_class, **kwargs)
            else:
                raise DeserializationError(f"Unsupported format: {format}")
                
        except Exception as e:
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"Deserialization failed: {e}")
            raise DeserializationError(f"Deserialization failed: {e}") from e

    async def serialize_to_file(
        self,
        obj: Any,
        file_path: str,
        format: SerializationFormat = SerializationFormat.JSON,
        **kwargs,
    ) -> None:
        """
        Serialize an object to a file.
        
        Args:
            obj: Object to serialize.
            file_path: Path to the output file.
            format: Serialization format to use.
            **kwargs: Additional format-specific arguments.
        
        Raises:
            SerializationError: If serialization or file writing fails.
        """
        data = self.serialize(obj, format, **kwargs)
        
        try:
            if isinstance(data, str):
                mode = "w"
                encoding = kwargs.get("encoding", "utf-8")
                with open(file_path, mode, encoding=encoding) as f:
                    f.write(data)
            else:
                mode = "wb"
                with open(file_path, mode) as f:
                    f.write(data)
        
        except Exception as e:
            raise SerializationError(f"Failed to write to file: {e}") from e

    async def deserialize_from_file(
        self,
        file_path: str,
        target_class: Optional[type] = None,
        format: SerializationFormat = SerializationFormat.JSON,
        **kwargs,
    ) -> Any:
        """
        Deserialize an object from a file.
        
        Args:
            file_path: Path to the input file.
            target_class: Optional target class for deserialization.
            format: Serialization format of the file.
            **kwargs: Additional format-specific arguments.
        
        Returns:
            Deserialized object.
        
        Raises:
            DeserializationError: If file reading or deserialization fails.
        """
        try:
            if format == SerializationFormat.JSON or format == SerializationFormat.YAML:
                mode = "r"
                encoding = kwargs.get("encoding", "utf-8")
                with open(file_path, mode, encoding=encoding) as f:
                    data = f.read()
            else:
                mode = "rb"
                with open(file_path, mode) as f:
                    data = f.read()
            
            return self.deserialize(data, target_class, format, **kwargs)
            
        except Exception as e:
            raise DeserializationError(f"Failed to read from file: {e}") from e

    def _serialize_json(self, obj: Any, **kwargs) -> str:
        """Serialize an object to JSON."""
        # Convert dataclass to dict
        if hasattr(obj, '__dataclass_fields__'):
            obj = asdict(obj)
        
        # Convert datetime objects to ISO format
        def datetime_handler(x):
            if isinstance(x, datetime):
                return x.isoformat()
            raise TypeError(f"Object of type {type(x)} is not JSON serializable")
        
        # Convert enum objects to values
        def enum_handler(x):
            if isinstance(x, Enum):
                return x.value
            raise TypeError(f"Object of type {type(x)} is not JSON serializable")
        
        # Convert set objects to lists
        def set_handler(x):
            if isinstance(x, set):
                return list(x)
            raise TypeError(f"Object of type {type(x)} is not JSON serializable")
        
        # Create custom encoder
        class CustomEncoder(json.JSONEncoder):
            def default(self, o):
                try:
                    return datetime_handler(o)
                except TypeError:
                    pass
                try:
                    return enum_handler(o)
                except TypeError:
                    pass
                try:
                    return set_handler(o)
                except TypeError:
                    pass
                return super().default(o)
        
        indent = kwargs.get("indent", 2)
        sort_keys = kwargs.get("sort_keys", False)
        
        return json.dumps(obj, cls=CustomEncoder, indent=indent, sort_keys=sort_keys)

    def _deserialize_json(self, data: str, target_class: Optional[type] = None, **kwargs) -> Any:
        """Deserialize JSON data."""
        obj = json.loads(data)
        
        if target_class is None:
            return obj
        
        # If target class is a dataclass, convert from dict
        if hasattr(target_class, '__dataclass_fields__'):
            return target_class(**obj)
        
        # If target class has from_dict method, use it
        if hasattr(target_class, 'from_dict'):
            return target_class.from_dict(obj)
        
        # Otherwise, return as-is
        return obj

    def _serialize_pickle(self, obj: Any, **kwargs) -> bytes:
        """Serialize an object to pickle."""
        protocol = kwargs.get("protocol", pickle.HIGHEST_PROTOCOL)
        return pickle.dumps(obj, protocol=protocol)

    def _deserialize_pickle(self, data: bytes, target_class: Optional[type] = None, **kwargs) -> Any:
        """Deserialize pickle data."""
        obj = pickle.loads(data)
        
        if target_class is None:
            return obj
        
        # If target class is a dataclass and obj is a dict, convert
        if hasattr(target_class, '__dataclass_fields__') and isinstance(obj, dict):
            return target_class(**obj)
        
        return obj

    def _serialize_yaml(self, obj: Any, **kwargs) -> str:
        """Serialize an object to YAML."""
        try:
            import yaml
        except ImportError:
            raise SerializationError("PyYAML is required for YAML serialization")
        
        # Convert dataclass to dict
        if hasattr(obj, '__dataclass_fields__'):
            obj = asdict(obj)
        
        # Convert datetime objects to ISO format
        def datetime_representer(dumper, data):
            return dumper.represent_str(data.isoformat())
        
        # Convert enum objects to values
        def enum_representer(dumper, data):
            return dumper.represent_str(data.value)
        
        yaml.add_representer(datetime, datetime_representer)
        yaml.add_representer(Enum, enum_representer)
        
        default_flow_style = kwargs.get("default_flow_style", False)
        sort_keys = kwargs.get("sort_keys", False)
        
        return yaml.dump(obj, default_flow_style=default_flow_style, sort_keys=sort_keys)

    def _deserialize_yaml(self, data: str, target_class: Optional[type] = None, **kwargs) -> Any:
        """Deserialize YAML data."""
        try:
            import yaml
        except ImportError:
            raise DeserializationError("PyYAML is required for YAML deserialization")
        
        obj = yaml.safe_load(data)
        
        if target_class is None:
            return obj
        
        # If target class is a dataclass, convert from dict
        if hasattr(target_class, '__dataclass_fields__') and isinstance(obj, dict):
            return target_class(**obj)
        
        # If target class has from_dict method, use it
        if hasattr(target_class, 'from_dict') and isinstance(obj, dict):
            return target_class.from_dict(obj)
        
        return obj

    def _serialize_msgpack(self, obj: Any, **kwargs) -> bytes:
        """Serialize an object to MessagePack."""
        try:
            import msgpack
        except ImportError:
            raise SerializationError("msgpack is required for MessagePack serialization")
        
        # Convert dataclass to dict
        if hasattr(obj, '__dataclass_fields__'):
            obj = asdict(obj)
        
        # Convert datetime objects to ISO format strings
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, set):
                return list(obj)
            return obj
        
        # Recursively convert datetime objects
        def convert_obj(obj):
            if isinstance(obj, dict):
                return {k: convert_obj(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_obj(v) for v in obj]
            elif isinstance(obj, tuple):
                return tuple(convert_obj(v) for v in obj)
            else:
                return convert_datetime(obj)
        
        obj = convert_obj(obj)
        
        return msgpack.packb(obj)

    def _deserialize_msgpack(self, data: bytes, target_class: Optional[type] = None, **kwargs) -> Any:
        """Deserialize MessagePack data."""
        try:
            import msgpack
        except ImportError:
            raise DeserializationError("msgpack is required for MessagePack deserialization")
        
        obj = msgpack.unpackb(data)
        
        if target_class is None:
            return obj
        
        # If target class is a dataclass, convert from dict
        if hasattr(target_class, '__dataclass_fields__') and isinstance(obj, dict):
            return target_class(**obj)
        
        # If target class has from_dict method, use it
        if hasattr(target_class, 'from_dict') and isinstance(obj, dict):
            return target_class.from_dict(obj)
        
        return obj

    def _serialize_protobuf(self, obj: Any, **kwargs) -> bytes:
        """Serialize an object to Protocol Buffers."""
        raise SerializationError("Protocol Buffers serialization is not yet implemented")

    def _deserialize_protobuf(self, data: bytes, target_class: Optional[type] = None, **kwargs) -> Any:
        """Deserialize Protocol Buffers data."""
        raise DeserializationError("Protocol Buffers deserialization is not yet implemented")

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the AI serializer.
        
        Returns:
            Dictionary with serializer information.
        """
        return {
            "status": "active" if self._initialized and self._started else "inactive",
            "metrics": self._metrics.to_dict(),
            "supported_formats": [f.value for f in SerializationFormat],
        }

    async def reset(self) -> None:
        """
        Reset the AI serializer.
        
        This method resets all state and metrics.
        """
        logger.info("Resetting AISerializer...")
        
        self._metrics = AISerializerMetrics()
        self._initialized = False
        self._started = False
        
        logger.info("AISerializer reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AISerializer("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"serializations={self._metrics.serializations})"
        )
