from __future__ import annotations

from threading import RLock
from uuid import uuid4

from .models import SecurityContext, SecurityMetadata


class SecurityContextManager:
    """Manage security contexts and context propagation for runtime operations."""

    def __init__(self) -> None:
        self._contexts: dict[str, SecurityContext] = {}
        self._lock = RLock()

    def create_context(self, subject_id: str, resource: str, action: str, *, metadata: dict[str, object] | None = None) -> SecurityContext:
        context = SecurityContext(
            context_id=str(uuid4()),
            subject_id=subject_id,
            resource=resource,
            action=action,
            metadata=metadata or {},
        )
        with self._lock:
            self._contexts[context.context_id] = context
        return context

    def get_context(self, context_id: str) -> SecurityContext | None:
        with self._lock:
            return self._contexts.get(context_id)

    def update_context(self, context_id: str, **updates: object) -> SecurityContext | None:
        with self._lock:
            context = self._contexts.get(context_id)
            if context is None:
                return None
            updated = SecurityContext(
                context_id=context.context_id,
                subject_id=context.subject_id,
                resource=context.resource,
                action=context.action,
                source=context.source,
                metadata={**context.metadata, **dict(updates)},
            )
            self._contexts[context_id] = updated
            return updated

    def list_contexts(self) -> list[SecurityContext]:
        with self._lock:
            return list(self._contexts.values())
