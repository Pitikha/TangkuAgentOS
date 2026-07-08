#!/usr/bin/env python3
"""
Storage backends for the TangkuAgentOS Memory Engine.

This module implements various storage backends for persisting memory data.
Each backend provides a consistent interface for CRUD operations.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, AsyncIterator

import aiosqlite
import redis.asyncio as redis

from .interfaces import IMemoryBackend
from .models import Memory, MemoryMetadata, MemoryType
from .exceptions import (
    MemoryBackendError,
    MemoryBackendConnectionError,
    MemoryBackendTimeoutError,
    MemoryNotFoundError,
    MemoryValidationError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Base Storage Backend
# =============================================================================


@dataclass
class BackendConfig:
    """Configuration for a storage backend."""
    backend_type: str
    connection_string: str
    timeout: float = 30.0
    max_retries: int = 3
    pool_size: int = 10
    pool_timeout: float = 60.0
    extra: Dict[str, Any] = field(default_factory=dict)


class BaseStorageBackend(IMemoryBackend):
    """
    Base class for all storage backends.
    
    This class provides common functionality and implements the IMemoryBackend
    interface. Subclasses should implement the backend-specific operations.
    """
    
    def __init__(self, config: Optional[BackendConfig] = None):
        """
        Initialize the storage backend.
        
        Args:
            config: Configuration for the backend
        """
        self.config = config or BackendConfig(
            backend_type="base",
            connection_string="",
        )
        self._connected = False
        self._connection = None
        self._lock = asyncio.Lock()
    
    @property
    def backend_type(self) -> str:
        """Get the backend type."""
        return self.config.backend_type
    
    async def connect(self, **kwargs: Any) -> None:
        """Establish a connection to the backend."""
        async with self._lock:
            if self._connected:
                return
            
            try:
                await self._connect(**kwargs)
                self._connected = True
                logger.info(f"Connected to {self.backend_type} backend")
            except Exception as e:
                raise MemoryBackendConnectionError(
                    backend=self.backend_type,
                    connection_string=self.config.connection_string,
                    message=f"Connection failed: {e}",
                    cause=e,
                ) from e
    
    async def disconnect(self) -> None:
        """Close the connection to the backend."""
        async with self._lock:
            if not self._connected:
                return
            
            try:
                await self._disconnect()
                self._connected = False
                logger.info(f"Disconnected from {self.backend_type} backend")
            except Exception as e:
                logger.error(f"Error disconnecting from {self.backend_type}: {e}")
                raise MemoryBackendError(
                    backend=self.backend_type,
                    message=f"Disconnection failed: {e}",
                    cause=e,
                ) from e
    
    async def is_connected(self) -> bool:
        """Check if the backend is connected."""
        return self._connected
    
    async def _connect(self, **kwargs: Any) -> None:
        """
        Backend-specific connection logic.
        
        Subclasses should override this method to implement their connection logic.
        """
        pass
    
    async def _disconnect(self) -> None:
        """
        Backend-specific disconnection logic.
        
        Subclasses should override this method to implement their disconnection logic.
        """
        pass
    
    async def create(self, data: Dict[str, Any]) -> str:
        """Create a new record in the backend."""
        if not self._connected:
            await self.connect()
        
        # Generate a unique ID if not provided
        record_id = data.get("memory_id") or str(self._generate_id())
        data["memory_id"] = record_id
        
        # Add timestamps
        now = self._get_current_timestamp()
        data.setdefault("created_at", now)
        data.setdefault("updated_at", now)
        
        await self._create(record_id, data)
        return record_id
    
    async def read(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Read a record from the backend."""
        if not self._connected:
            await self.connect()
        
        return await self._read(record_id)
    
    async def update(self, record_id: str, data: Dict[str, Any]) -> bool:
        """Update a record in the backend."""
        if not self._connected:
            await self.connect()
        
        # Update the updated_at timestamp
        data["updated_at"] = self._get_current_timestamp()
        
        return await self._update(record_id, data)
    
    async def delete(self, record_id: str) -> bool:
        """Delete a record from the backend."""
        if not self._connected:
            await self.connect()
        
        return await self._delete(record_id)
    
    async def query(
        self,
        query: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a query against the backend."""
        if not self._connected:
            await self.connect()
        
        return await self._query(query, limit, offset)
    
    async def count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """Count records matching a query."""
        if not self._connected:
            await self.connect()
        
        return await self._count(query)
    
    async def begin_transaction(self) -> Any:
        """Begin a new transaction."""
        if not self._connected:
            await self.connect()
        
        return await self._begin_transaction()
    
    async def commit_transaction(self, transaction: Any) -> None:
        """Commit a transaction."""
        await self._commit_transaction(transaction)
    
    async def rollback_transaction(self, transaction: Any) -> None:
        """Rollback a transaction."""
        await self._rollback_transaction(transaction)
    
    async def backup(self, path: str) -> None:
        """Create a backup of the backend data."""
        await self._backup(path)
    
    async def restore(self, path: str) -> None:
        """Restore data from a backup."""
        await self._restore(path)
    
    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for transactions.
        
        Example:
            async with backend.transaction():
                await backend.create({"key": "value1"})
                await backend.create({"key": "value2"})
        """
        transaction = await self.begin_transaction()
        try:
            yield transaction
            await self.commit_transaction(transaction)
        except Exception:
            await self.rollback_transaction(transaction)
            raise
    
    def _generate_id(self) -> str:
        """Generate a unique ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _get_current_timestamp(self) -> str:
        """Get the current timestamp as an ISO string."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    # Abstract methods to be implemented by subclasses
    @abstractmethod
    async def _create(self, record_id: str, data: Dict[str, Any]) -> None:
        """Backend-specific create operation."""
        pass
    
    @abstractmethod
    async def _read(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Backend-specific read operation."""
        pass
    
    @abstractmethod
    async def _update(self, record_id: str, data: Dict[str, Any]) -> bool:
        """Backend-specific update operation."""
        pass
    
    @abstractmethod
    async def _delete(self, record_id: str) -> bool:
        """Backend-specific delete operation."""
        pass
    
    @abstractmethod
    async def _query(
        self,
        query: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Backend-specific query operation."""
        pass
    
    @abstractmethod
    async def _count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """Backend-specific count operation."""
        pass
    
    @abstractmethod
    async def _begin_transaction(self) -> Any:
        """Backend-specific begin transaction operation."""
        pass
    
    @abstractmethod
    async def _commit_transaction(self, transaction: Any) -> None:
        """Backend-specific commit transaction operation."""
        pass
    
    @abstractmethod
    async def _rollback_transaction(self, transaction: Any) -> None:
        """Backend-specific rollback transaction operation."""
        pass
    
    @abstractmethod
    async def _backup(self, path: str) -> None:
        """Backend-specific backup operation."""
        pass
    
    @abstractmethod
    async def _restore(self, path: str) -> None:
        """Backend-specific restore operation."""
        pass


# =============================================================================
# SQLite Backend
# =============================================================================


class SQLiteBackend(BaseStorageBackend):
    """
    SQLite storage backend for the Memory Engine.
    
    This backend stores memory data in a SQLite database, providing
    persistent storage with ACID transactions.
    
    Attributes:
        db_path: Path to the SQLite database file
        connection: Async SQLite connection
    """
    
    def __init__(self, db_path: Union[str, Path] = ":memory:", **kwargs):
        """
        Initialize the SQLite backend.
        
        Args:
            db_path: Path to the SQLite database file
            **kwargs: Additional configuration
        """
        self.db_path = Path(db_path)
        self.connection: Optional[aiosqlite.Connection] = None
        
        config = BackendConfig(
            backend_type="sqlite",
            connection_string=str(db_path),
            timeout=kwargs.get("timeout", 30.0),
            max_retries=kwargs.get("max_retries", 3),
        )
        super().__init__(config)
    
    async def _connect(self, **kwargs: Any) -> None:
        """Connect to the SQLite database."""
        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row
        
        # Enable WAL mode for better concurrency
        await self.connection.execute("PRAGMA journal_mode=WAL")
        await self.connection.execute("PRAGMA synchronous=NORMAL")
        
        # Create tables if they don't exist
        await self._create_tables()
        await self.connection.commit()
    
    async def _disconnect(self) -> None:
        """Disconnect from the SQLite database."""
        if self.connection:
            await self.connection.close()
            self.connection = None
    
    async def _create_tables(self) -> None:
        """Create the necessary database tables."""
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT,
                tags TEXT,
                source TEXT,
                author TEXT,
                importance REAL DEFAULT 0.5,
                confidence REAL DEFAULT 0.5,
                version INTEGER DEFAULT 1,
                parent_id TEXT,
                references TEXT,
                permissions TEXT,
                custom TEXT,
                embedding BLOB,
                raw TEXT
            )
        """)
        
        await self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_type 
            ON memories(memory_type)
        """)
        
        await self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON memories(created_at)
        """)
        
        await self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_tags 
            ON memories(tags)
        """)
        
        await self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_importance 
            ON memories(importance)
        """)
    
    async def _create(self, record_id: str, data: Dict[str, Any]) -> None:
        """Create a new record in SQLite."""
        # Convert complex types to JSON strings
        data_copy = data.copy()
        data_copy["tags"] = json.dumps(data_copy.get("tags", []))
        data_copy["references"] = json.dumps(data_copy.get("references", []))
        data_copy["permissions"] = json.dumps(data_copy.get("permissions", {}))
        data_copy["custom"] = json.dumps(data_copy.get("custom", {}))
        data_copy["embedding"] = json.dumps(data_copy.get("embedding", []))
        data_copy["raw"] = json.dumps(data_copy.get("raw", {}))
        
        columns = ", ".join(data_copy.keys())
        placeholders = ", ".join(["?"] * len(data_copy))
        values = list(data_copy.values())
        
        query = f"INSERT INTO memories ({columns}) VALUES ({placeholders})"
        await self.connection.execute(query, values)
        await self.connection.commit()
    
    async def _read(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Read a record from SQLite."""
        cursor = await self.connection.execute(
            "SELECT * FROM memories WHERE memory_id = ?",
            (record_id,),
        )
        row = await cursor.fetchone()
        
        if not row:
            return None
        
        # Convert JSON strings back to Python objects
        data = dict(row)
        data["tags"] = json.loads(data.get("tags", "[]"))
        data["references"] = json.loads(data.get("references", "[]"))
        data["permissions"] = json.loads(data.get("permissions", "{}"))
        data["custom"] = json.loads(data.get("custom", "{}"))
        data["embedding"] = json.loads(data.get("embedding", "[]"))
        data["raw"] = json.loads(data.get("raw", "{}"))
        
        return data
    
    async def _update(self, record_id: str, data: Dict[str, Any]) -> bool:
        """Update a record in SQLite."""
        # Convert complex types to JSON strings
        data_copy = data.copy()
        data_copy["tags"] = json.dumps(data_copy.get("tags", []))
        data_copy["references"] = json.dumps(data_copy.get("references", []))
        data_copy["permissions"] = json.dumps(data_copy.get("permissions", {}))
        data_copy["custom"] = json.dumps(data_copy.get("custom", {}))
        data_copy["embedding"] = json.dumps(data_copy.get("embedding", []))
        data_copy["raw"] = json.dumps(data_copy.get("raw", {}))
        
        # Remove memory_id from update data
        data_copy.pop("memory_id", None)
        
        if not data_copy:
            return False
        
        set_clause = ", ".join([f"{k} = ?" for k in data_copy.keys()])
        values = list(data_copy.values())
        values.append(record_id)
        
        query = f"UPDATE memories SET {set_clause} WHERE memory_id = ?"
        cursor = await self.connection.execute(query, values)
        await self.connection.commit()
        
        return cursor.rowcount > 0
    
    async def _delete(self, record_id: str) -> bool:
        """Delete a record from SQLite."""
        cursor = await self.connection.execute(
            "DELETE FROM memories WHERE memory_id = ?",
            (record_id,),
        )
        await self.connection.commit()
        return cursor.rowcount > 0
    
    async def _query(
        self,
        query: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a query against SQLite."""
        # Build WHERE clause
        conditions = []
        params = []
        
        for key, value in query.items():
            if key == "memory_type":
                conditions.append(f"memory_type = ?")
                params.append(value)
            elif key == "tags":
                # JSON array contains tag
                conditions.append(f"json_contains(tags, ?)")
                params.append(json.dumps([value]))
            elif key == "created_after":
                conditions.append(f"created_at >= ?")
                params.append(value)
            elif key == "created_before":
                conditions.append(f"created_at <= ?")
                params.append(value)
            elif key == "min_importance":
                conditions.append(f"importance >= ?")
                params.append(value)
            elif key == "max_importance":
                conditions.append(f"importance <= ?")
                params.append(value)
            # Add more conditions as needed
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Build LIMIT and OFFSET
        limit_clause = ""
        if limit is not None:
            limit_clause += f" LIMIT {limit}"
        if offset is not None:
            limit_clause += f" OFFSET {offset}"
        
        query_str = f"SELECT * FROM memories WHERE {where_clause}{limit_clause}"
        cursor = await self.connection.execute(query_str, params)
        rows = await cursor.fetchall()
        
        # Convert rows to dictionaries and parse JSON fields
        results = []
        for row in rows:
            data = dict(row)
            data["tags"] = json.loads(data.get("tags", "[]"))
            data["references"] = json.loads(data.get("references", "[]"))
            data["permissions"] = json.loads(data.get("permissions", "{}"))
            data["custom"] = json.loads(data.get("custom", "{}"))
            data["embedding"] = json.loads(data.get("embedding", "[]"))
            data["raw"] = json.loads(data.get("raw", "{}"))
            results.append(data)
        
        return results
    
    async def _count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """Count records in SQLite."""
        if not query:
            cursor = await self.connection.execute("SELECT COUNT(*) FROM memories")
            row = await cursor.fetchone()
            return row[0]
        
        # Build WHERE clause
        conditions = []
        params = []
        
        for key, value in query.items():
            if key == "memory_type":
                conditions.append(f"memory_type = ?")
                params.append(value)
            elif key == "tags":
                conditions.append(f"json_contains(tags, ?)")
                params.append(json.dumps([value]))
            # Add more conditions as needed
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query_str = f"SELECT COUNT(*) FROM memories WHERE {where_clause}"
        cursor = await self.connection.execute(query_str, params)
        row = await cursor.fetchone()
        return row[0]
    
    async def _begin_transaction(self) -> Any:
        """Begin a new SQLite transaction."""
        await self.connection.execute("BEGIN")
        return "sqlite_transaction"
    
    async def _commit_transaction(self, transaction: Any) -> None:
        """Commit a SQLite transaction."""
        await self.connection.commit()
    
    async def _rollback_transaction(self, transaction: Any) -> None:
        """Rollback a SQLite transaction."""
        await self.connection.rollback()
    
    async def _backup(self, path: str) -> None:
        """Create a backup of the SQLite database."""
        # Use sqlite3 for backup (synchronous but fast)
        import sqlite3
        
        backup_path = Path(path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Close the async connection temporarily
        if self.connection:
            await self.connection.close()
            self.connection = None
        
        # Create backup
        conn = sqlite3.connect(str(self.db_path))
        backup_conn = sqlite3.connect(str(backup_path))
        conn.backup(backup_conn)
        backup_conn.close()
        conn.close()
        
        # Reopen the async connection
        await self._connect()
    
    async def _restore(self, path: str) -> None:
        """Restore SQLite database from a backup."""
        import sqlite3
        
        backup_path = Path(path)
        if not backup_path.exists():
            raise MemoryBackendError(
                backend=self.backend_type,
                message=f"Backup file not found: {path}",
            )
        
        # Close the async connection temporarily
        if self.connection:
            await self.connection.close()
            self.connection = None
        
        # Restore from backup
        conn = sqlite3.connect(str(self.db_path))
        backup_conn = sqlite3.connect(str(backup_path))
        backup_conn.backup(conn)
        conn.close()
        backup_conn.close()
        
        # Reopen the async connection
        await self._connect()


# =============================================================================
# PostgreSQL Backend
# =============================================================================


class PostgreSQLBackend(BaseStorageBackend):
    """
    PostgreSQL storage backend for the Memory Engine.
    
    This backend stores memory data in a PostgreSQL database, providing
    scalable, persistent storage with ACID transactions.
    
    Attributes:
        connection_string: PostgreSQL connection string
        pool: Async connection pool
    """
    
    def __init__(self, connection_string: str, **kwargs):
        """
        Initialize the PostgreSQL backend.
        
        Args:
            connection_string: PostgreSQL connection string
            **kwargs: Additional configuration
        """
        self.connection_string = connection_string
        self.pool = None
        
        config = BackendConfig(
            backend_type="postgresql",
            connection_string=connection_string,
            timeout=kwargs.get("timeout", 30.0),
            max_retries=kwargs.get("max_retries", 3),
            pool_size=kwargs.get("pool_size", 10),
            pool_timeout=kwargs.get("pool_timeout", 60.0),
        )
        super().__init__(config)
    
    async def _connect(self, **kwargs: Any) -> None:
        """Connect to the PostgreSQL database."""
        try:
            import asyncpg
        except ImportError:
            raise MemoryBackendError(
                backend=self.backend_type,
                message="asyncpg is required for PostgreSQL backend. Install with: pip install asyncpg",
            )
        
        self.pool = await asyncpg.create_pool(
            dsn=self.connection_string,
            min_size=1,
            max_size=self.config.pool_size,
            max_queries=self.config.pool_size * 2,
            max_inactive_connection_lifetime=self.config.pool_timeout,
        )
        
        # Create tables if they don't exist
        await self._create_tables()
    
    async def _disconnect(self) -> None:
        """Disconnect from the PostgreSQL database."""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def _create_tables(self) -> None:
        """Create the necessary database tables."""
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                memory_id UUID PRIMARY KEY,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                expires_at TIMESTAMPTZ,
                tags TEXT[],
                source TEXT,
                author TEXT,
                importance NUMERIC DEFAULT 0.5,
                confidence NUMERIC DEFAULT 0.5,
                version INTEGER DEFAULT 1,
                parent_id UUID,
                references UUID[],
                permissions JSONB DEFAULT '{}',
                custom JSONB DEFAULT '{}',
                embedding NUMERIC[],
                raw JSONB DEFAULT '{}'
            )
        """)
        
        await self.pool.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_type 
            ON memories(memory_type)
        """)
        
        await self.pool.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON memories(created_at)
        """)
        
        await self.pool.execute("""
            CREATE INDEX IF NOT EXISTS idx_tags 
            ON memories USING GIN(tags)
        """)
        
        await self.pool.execute("""
            CREATE INDEX IF NOT EXISTS idx_importance 
            ON memories(importance)
        """)
        
        await self.pool.execute("""
            CREATE INDEX IF NOT EXISTS idx_embedding 
            ON memories USING HNSW(embedding vector_l2_ops)
        """)
    
    async def _create(self, record_id: str, data: Dict[str, Any]) -> None:
        """Create a new record in PostgreSQL."""
        # Convert UUID strings to UUID objects
        data_copy = data.copy()
        data_copy["memory_id"] = uuid.UUID(record_id)
        if data_copy.get("parent_id"):
            data_copy["parent_id"] = uuid.UUID(data_copy["parent_id"])
        
        # Convert references to UUID array
        if "references" in data_copy:
            data_copy["references"] = [uuid.UUID(ref) for ref in data_copy["references"]]
        
        columns = ", ".join(data_copy.keys())
        placeholders = ", ".join([f"${i+1}" for i in range(len(data_copy))])
        values = list(data_copy.values())
        
        query = f"INSERT INTO memories ({columns}) VALUES ({placeholders})"
        await self.pool.execute(query, *values)
    
    async def _read(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Read a record from PostgreSQL."""
        row = await self.pool.fetchrow(
            "SELECT * FROM memories WHERE memory_id = $1",
            uuid.UUID(record_id),
        )
        
        if not row:
            return None
        
        # Convert UUID objects back to strings
        data = dict(row)
        data["memory_id"] = str(data["memory_id"])
        if data.get("parent_id"):
            data["parent_id"] = str(data["parent_id"])
        
        # Convert references to strings
        if data.get("references"):
            data["references"] = [str(ref) for ref in data["references"]]
        
        # Convert timestamps to ISO strings
        for timestamp_field in ["created_at", "updated_at", "expires_at"]:
            if data.get(timestamp_field):
                data[timestamp_field] = data[timestamp_field].isoformat()
        
        return data
    
    async def _update(self, record_id: str, data: Dict[str, Any]) -> bool:
        """Update a record in PostgreSQL."""
        # Convert UUID strings to UUID objects
        data_copy = data.copy()
        if "parent_id" in data_copy and data_copy["parent_id"]:
            data_copy["parent_id"] = uuid.UUID(data_copy["parent_id"])
        
        # Convert references to UUID array
        if "references" in data_copy:
            data_copy["references"] = [uuid.UUID(ref) for ref in data_copy["references"]]
        
        # Remove memory_id from update data
        data_copy.pop("memory_id", None)
        
        if not data_copy:
            return False
        
        set_clause = ", ".join([f"{k} = ${i+1}" for i, k in enumerate(data_copy.keys())])
        values = list(data_copy.values())
        values.append(uuid.UUID(record_id))
        
        query = f"UPDATE memories SET {set_clause} WHERE memory_id = ${len(data_copy)+1}"
        result = await self.pool.execute(query, *values)
        
        return result.split(" ")[1] != "0"
    
    async def _delete(self, record_id: str) -> bool:
        """Delete a record from PostgreSQL."""
        result = await self.pool.execute(
            "DELETE FROM memories WHERE memory_id = $1",
            uuid.UUID(record_id),
        )
        return result.split(" ")[1] != "0"
    
    async def _query(
        self,
        query: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a query against PostgreSQL."""
        # Build WHERE clause
        conditions = []
        params = []
        param_index = 1
        
        for key, value in query.items():
            if key == "memory_type":
                conditions.append(f"memory_type = ${param_index}")
                params.append(value)
                param_index += 1
            elif key == "tags":
                conditions.append(f"$${param_index} = ANY(tags)")
                params.append(value)
                param_index += 1
            elif key == "created_after":
                conditions.append(f"created_at >= $${param_index}")
                params.append(value)
                param_index += 1
            elif key == "created_before":
                conditions.append(f"created_at <= $${param_index}")
                params.append(value)
                param_index += 1
            elif key == "min_importance":
                conditions.append(f"importance >= $${param_index}")
                params.append(value)
                param_index += 1
            elif key == "max_importance":
                conditions.append(f"importance <= $${param_index}")
                params.append(value)
                param_index += 1
            # Add more conditions as needed
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        # Build LIMIT and OFFSET
        limit_clause = ""
        if limit is not None:
            limit_clause += f" LIMIT {limit}"
        if offset is not None:
            limit_clause += f" OFFSET {offset}"
        
        query_str = f"SELECT * FROM memories WHERE {where_clause}{limit_clause}"
        rows = await self.pool.fetch(query_str, *params)
        
        # Convert rows to dictionaries
        results = []
        for row in rows:
            data = dict(row)
            data["memory_id"] = str(data["memory_id"])
            if data.get("parent_id"):
                data["parent_id"] = str(data["parent_id"])
            if data.get("references"):
                data["references"] = [str(ref) for ref in data["references"]]
            for timestamp_field in ["created_at", "updated_at", "expires_at"]:
                if data.get(timestamp_field):
                    data[timestamp_field] = data[timestamp_field].isoformat()
            results.append(data)
        
        return results
    
    async def _count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """Count records in PostgreSQL."""
        if not query:
            row = await self.pool.fetchrow("SELECT COUNT(*) FROM memories")
            return row[0]
        
        # Build WHERE clause
        conditions = []
        params = []
        param_index = 1
        
        for key, value in query.items():
            if key == "memory_type":
                conditions.append(f"memory_type = ${param_index}")
                params.append(value)
                param_index += 1
            elif key == "tags":
                conditions.append(f"$${param_index} = ANY(tags)")
                params.append(value)
                param_index += 1
            # Add more conditions as needed
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        query_str = f"SELECT COUNT(*) FROM memories WHERE {where_clause}"
        row = await self.pool.fetchrow(query_str, *params)
        return row[0]
    
    async def _begin_transaction(self) -> Any:
        """Begin a new PostgreSQL transaction."""
        return await self.pool.begin()
    
    async def _commit_transaction(self, transaction: Any) -> None:
        """Commit a PostgreSQL transaction."""
        await transaction.commit()
    
    async def _rollback_transaction(self, transaction: Any) -> None:
        """Rollback a PostgreSQL transaction."""
        await transaction.rollback()
    
    async def _backup(self, path: str) -> None:
        """Create a backup of the PostgreSQL database."""
        # Use pg_dump for backup
        import subprocess
        
        backup_path = Path(path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            result = subprocess.run(
                ["pg_dump", self.connection_string, "-Fc", "-f", str(backup_path)],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise MemoryBackendError(
                backend=self.backend_type,
                message=f"Backup failed: {e.stderr.decode()}",
                cause=e,
            )
    
    async def _restore(self, path: str) -> None:
        """Restore PostgreSQL database from a backup."""
        import subprocess
        
        backup_path = Path(path)
        if not backup_path.exists():
            raise MemoryBackendError(
                backend=self.backend_type,
                message=f"Backup file not found: {path}",
            )
        
        try:
            result = subprocess.run(
                ["pg_restore", "-d", self.connection_string, "-Fc", str(backup_path)],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise MemoryBackendError(
                backend=self.backend_type,
                message=f"Restore failed: {e.stderr.decode()}",
                cause=e,
            )


# =============================================================================
# Redis Backend
# =============================================================================


class RedisBackend(BaseStorageBackend):
    """
    Redis storage backend for the Memory Engine.
    
    This backend stores memory data in Redis, providing fast, in-memory storage
    with optional persistence.
    
    Attributes:
        redis: Redis async client
        prefix: Key prefix for memory data
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", **kwargs):
        """
        Initialize the Redis backend.
        
        Args:
            redis_url: Redis connection URL
            **kwargs: Additional configuration
        """
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.prefix = kwargs.get("prefix", "tangku_memory:")
        
        config = BackendConfig(
            backend_type="redis",
            connection_string=redis_url,
            timeout=kwargs.get("timeout", 30.0),
            max_retries=kwargs.get("max_retries", 3),
        )
        super().__init__(config)
    
    async def _connect(self, **kwargs: Any) -> None:
        """Connect to Redis."""
        self.redis = redis.from_url(
            self.redis_url,
            decode_responses=True,
            socket_timeout=self.config.timeout,
            socket_connect_timeout=self.config.timeout,
        )
        
        # Test the connection
        await self.redis.ping()
    
    async def _disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None
    
    def _get_key(self, record_id: str) -> str:
        """Get the Redis key for a memory record."""
        return f"{self.prefix}{record_id}"
    
    async def _create(self, record_id: str, data: Dict[str, Any]) -> None:
        """Create a new record in Redis."""
        key = self._get_key(record_id)
        
        # Store the entire data as a JSON string
        await self.redis.hset(key, mapping=data)
        
        # Set expiration if specified
        if data.get("expires_at"):
            from datetime import datetime
            expires_at = datetime.fromisoformat(data["expires_at"])
            now = datetime.utcnow()
            ttl = (expires_at - now).total_seconds()
            if ttl > 0:
                await self.redis.expire(key, int(ttl))
        
        # Add to memory type index
        memory_type = data.get("memory_type", "unknown")
        await self.redis.sadd(f"{self.prefix}types:{memory_type}", record_id)
        
        # Add to tags index
        tags = data.get("tags", [])
        for tag in tags:
            await self.redis.sadd(f"{self.prefix}tags:{tag}", record_id)
        
        # Add to created_at index (sorted set)
        created_at = data.get("created_at", "")
        if created_at:
            from datetime import datetime
            timestamp = datetime.fromisoformat(created_at).timestamp()
            await self.redis.zadd(f"{self.prefix}created:", {record_id: timestamp})
    
    async def _read(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Read a record from Redis."""
        key = self._get_key(record_id)
        data = await self.redis.hgetall(key)
        
        if not data:
            return None
        
        # Convert numeric strings to appropriate types
        for field in ["importance", "confidence", "version"]:
            if field in data:
                try:
                    data[field] = float(data[field])
                    if field in ["version"]:
                        data[field] = int(data[field])
                except (ValueError, TypeError):
                    pass
        
        # Convert JSON strings back to Python objects
        for field in ["tags", "references", "permissions", "custom", "embedding", "raw"]:
            if field in data:
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        
        return data
    
    async def _update(self, record_id: str, data: Dict[str, Any]) -> bool:
        """Update a record in Redis."""
        key = self._get_key(record_id)
        
        # Check if the record exists
        if not await self.redis.exists(key):
            return False
        
        # Update the record
        await self.redis.hset(key, mapping=data)
        
        # Update expiration if specified
        if "expires_at" in data:
            from datetime import datetime
            expires_at = datetime.fromisoformat(data["expires_at"])
            now = datetime.utcnow()
            ttl = (expires_at - now).total_seconds()
            if ttl > 0:
                await self.redis.expire(key, int(ttl))
            else:
                await self.redis.persist(key)
        
        # Update tags index
        if "tags" in data:
            old_data = await self.redis.hgetall(key)
            old_tags = json.loads(old_data.get("tags", "[]"))
            new_tags = data.get("tags", [])
            
            # Remove old tags
            for tag in old_tags:
                if tag not in new_tags:
                    await self.redis.srem(f"{self.prefix}tags:{tag}", record_id)
            
            # Add new tags
            for tag in new_tags:
                if tag not in old_tags:
                    await self.redis.sadd(f"{self.prefix}tags:{tag}", record_id)
        
        return True
    
    async def _delete(self, record_id: str) -> bool:
        """Delete a record from Redis."""
        key = self._get_key(record_id)
        
        # Get the record to update indexes
        data = await self.redis.hgetall(key)
        if not data:
            return False
        
        # Remove from memory type index
        memory_type = data.get("memory_type", "unknown")
        await self.redis.srem(f"{self.prefix}types:{memory_type}", record_id)
        
        # Remove from tags index
        tags = json.loads(data.get("tags", "[]"))
        for tag in tags:
            await self.redis.srem(f"{self.prefix}tags:{tag}", record_id)
        
        # Remove from created_at index
        await self.redis.zrem(f"{self.prefix}created:", record_id)
        
        # Delete the record
        return await self.redis.delete(key) > 0
    
    async def _query(
        self,
        query: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a query against Redis."""
        # Get all memory IDs first
        memory_ids = set()
        
        # Filter by memory type
        if "memory_type" in query:
            memory_type = query["memory_type"]
            type_members = await self.redis.smembers(f"{self.prefix}types:{memory_type}")
            memory_ids.update(type_members)
        else:
            # Get all memory IDs from all types
            type_keys = await self.redis.keys(f"{self.prefix}types:*")
            for type_key in type_keys:
                type_members = await self.redis.smembers(type_key)
                memory_ids.update(type_members)
        
        # Filter by tags
        if "tags" in query:
            tag = query["tags"]
            tag_members = await self.redis.smembers(f"{self.prefix}tags:{tag}")
            if memory_ids:
                memory_ids.intersection_update(tag_members)
            else:
                memory_ids = tag_members
        
        # Convert to list and apply limit/offset
        memory_ids = list(memory_ids)
        if offset is not None:
            memory_ids = memory_ids[offset:]
        if limit is not None:
            memory_ids = memory_ids[:limit]
        
        # Get the actual memory data
        results = []
        for memory_id in memory_ids:
            data = await self._read(str(memory_id))
            if data:
                results.append(data)
        
        return results
    
    async def _count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """Count records in Redis."""
        if not query:
            # Count all memories across all types
            type_keys = await self.redis.keys(f"{self.prefix}types:*")
            total = 0
            for type_key in type_keys:
                total += await self.redis.scard(type_key)
            return total
        
        # Apply filters
        memory_ids = set()
        
        if "memory_type" in query:
            memory_type = query["memory_type"]
            memory_ids = await self.redis.smembers(f"{self.prefix}types:{memory_type}")
        else:
            type_keys = await self.redis.keys(f"{self.prefix}types:*")
            for type_key in type_keys:
                memory_ids.update(await self.redis.smembers(type_key))
        
        if "tags" in query:
            tag = query["tags"]
            tag_members = await self.redis.smembers(f"{self.prefix}tags:{tag}")
            memory_ids.intersection_update(tag_members)
        
        return len(memory_ids)
    
    async def _begin_transaction(self) -> Any:
        """Begin a new Redis transaction."""
        return await self.redis.multi()
    
    async def _commit_transaction(self, transaction: Any) -> None:
        """Commit a Redis transaction."""
        await transaction.exec()
    
    async def _rollback_transaction(self, transaction: Any) -> None:
        """Rollback a Redis transaction."""
        await transaction.discard()
    
    async def _backup(self, path: str) -> None:
        """Create a backup of the Redis database."""
        import subprocess
        
        backup_path = Path(path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            result = subprocess.run(
                ["redis-cli", "SAVE"],
                check=True,
                capture_output=True,
            )
            
            # Copy the dump file
            import shutil
            dump_path = Path("/var/lib/redis/dump.rdb")
            if dump_path.exists():
                shutil.copy(dump_path, backup_path)
        except Exception as e:
            raise MemoryBackendError(
                backend=self.backend_type,
                message=f"Backup failed: {e}",
                cause=e,
            )
    
    async def _restore(self, path: str) -> None:
        """Restore Redis database from a backup."""
        import subprocess
        
        backup_path = Path(path)
        if not backup_path.exists():
            raise MemoryBackendError(
                backend=self.backend_type,
                message=f"Backup file not found: {path}",
            )
        
        try:
            # Stop Redis saves
            subprocess.run(["redis-cli", "CONFIG", "SET", "save", ""], check=True)
            
            # Copy the backup file
            import shutil
            dump_path = Path("/var/lib/redis/dump.rdb")
            shutil.copy(backup_path, dump_path)
            
            # Restart Redis saves
            subprocess.run(
                ["redis-cli", "CONFIG", "SET", "save", "900 1"],
                check=True,
            )
            
            # Restart Redis to load the new data
            subprocess.run(["redis-cli", "SHUTDOWN", "SAVE"], check=True)
            subprocess.run(["redis-server", "--daemonize", "yes"], check=True)
        except Exception as e:
            raise MemoryBackendError(
                backend=self.backend_type,
                message=f"Restore failed: {e}",
                cause=e,
            )


# =============================================================================
# Backend Factory
# =============================================================================


class BackendFactory:
    """
    Factory for creating storage backends.
    
    This class provides a convenient way to create backend instances
    based on configuration.
    """
    
    @staticmethod
    def create_backend(
        backend_type: Union[str, MemoryBackendType],
        **kwargs: Any,
    ) -> BaseStorageBackend:
        """
        Create a storage backend of the specified type.
        
        Args:
            backend_type: Type of backend to create
            **kwargs: Configuration parameters for the backend
            
        Returns:
            An instance of the specified backend
            
        Raises:
            ValueError: If the backend type is not supported
        """
        if isinstance(backend_type, str):
            backend_type = MemoryBackendType[backend_type.upper()]
        
        if backend_type == MemoryBackendType.SQLITE:
            return SQLiteBackend(**kwargs)
        elif backend_type == MemoryBackendType.POSTGRESQL:
            return PostgreSQLBackend(**kwargs)
        elif backend_type == MemoryBackendType.REDIS:
            return RedisBackend(**kwargs)
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")
