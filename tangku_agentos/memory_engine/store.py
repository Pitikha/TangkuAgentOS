from __future__ import annotations

import os
import pickle
import sqlite3
from typing import Any

from .interfaces import MemoryStore
from .models import MemoryRecord, MemorySnapshot


class MemoryStoreImpl(MemoryStore):
    """SQLite-backed store for memory records and snapshots."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or ':memory:'
        self._connection: sqlite3.Connection | None = None
        self._connect()
        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        if self._connection is None:
            if self._db_path != ':memory:':
                directory = os.path.dirname(self._db_path)
                if directory:
                    os.makedirs(directory, exist_ok=True)
            self._connection = sqlite3.connect(self._db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def _initialize_schema(self) -> None:
        connection = self._connect()
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_records (
                record_id TEXT PRIMARY KEY,
                payload BLOB NOT NULL,
                namespace TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                payload BLOB NOT NULL,
                record_id TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.commit()

    def save(self, record: MemoryRecord) -> None:
        connection = self._connect()
        connection.execute(
            "INSERT INTO memory_records(record_id, payload, namespace, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(record_id) DO UPDATE SET payload=excluded.payload, namespace=excluded.namespace, updated_at=excluded.updated_at",
            (record.record_id, sqlite3.Binary(pickle.dumps(record)), record.namespace, self._timestamp()),
        )
        connection.commit()

    def retrieve(self, record_id: str) -> MemoryRecord:
        connection = self._connect()
        row = connection.execute(
            "SELECT payload FROM memory_records WHERE record_id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            raise KeyError(record_id)
        return pickle.loads(row["payload"])

    def delete(self, record_id: str) -> None:
        connection = self._connect()
        connection.execute("DELETE FROM memory_records WHERE record_id = ?", (record_id,))
        connection.commit()

    def list_all(self) -> dict[str, MemoryRecord]:
        connection = self._connect()
        rows = connection.execute("SELECT record_id, payload FROM memory_records").fetchall()
        return {row["record_id"]: pickle.loads(row["payload"]) for row in rows}

    def save_snapshot(self, snapshot: MemorySnapshot) -> None:
        connection = self._connect()
        connection.execute(
            "INSERT INTO memory_snapshots(snapshot_id, payload, record_id, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(snapshot_id) DO UPDATE SET payload=excluded.payload, record_id=excluded.record_id, updated_at=excluded.updated_at",
            (snapshot.snapshot_id, sqlite3.Binary(pickle.dumps(snapshot)), snapshot.record.record_id, self._timestamp()),
        )
        connection.commit()

    def list_snapshots(self) -> dict[str, MemorySnapshot]:
        connection = self._connect()
        rows = connection.execute("SELECT snapshot_id, payload FROM memory_snapshots").fetchall()
        return {row["snapshot_id"]: pickle.loads(row["payload"]) for row in rows}

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @staticmethod
    def _timestamp() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
