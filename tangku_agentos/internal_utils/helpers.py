from __future__ import annotations

from contextlib import contextmanager
from threading import RLock

_lock = RLock()

@contextmanager
def lock_manager():
    """Context manager for shared locking across internal utilities."""
    with _lock:
        yield
