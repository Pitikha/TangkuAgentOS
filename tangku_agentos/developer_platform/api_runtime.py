from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, List


@dataclass(frozen=True)
class APIContext:
    context_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class APIRoute:
    route_id: str
    method: str
    path: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class APIRouter:
    def __init__(self) -> None:
        self._routes: Dict[tuple[str, str], APIRoute] = {}
        self._lock = RLock()

    def register(self, path: str, method: str = "GET", metadata: dict[str, Any] | None = None) -> APIRoute:
        with self._lock:
            route = APIRoute(route_id=f"{method}:{path}", method=method, path=path, metadata=metadata or {})
            self._routes[(method, path)] = route
            return route


class APIManager:
    def __init__(self) -> None:
        self._routes: Dict[str, APIRouter] = {}
        self._lock = RLock()

    def register_route(self, route_id: str, router: APIRouter) -> None:
        with self._lock:
            self._routes[route_id] = router

    def get_route(self, route_id: str) -> APIRouter | None:
        with self._lock:
            return self._routes.get(route_id)


class APIRegistry:
    def __init__(self) -> None:
        self._routes: Dict[str, APIRoute] = {}
        self._lock = RLock()

    def register(self, route: APIRoute) -> None:
        with self._lock:
            self._routes[route.route_id] = route


class APIAuthentication:
    def __init__(self) -> None:
        self._tokens: Dict[str, str] = {}
        self._lock = RLock()

    def register_token(self, token: str, scope: str) -> None:
        with self._lock:
            self._tokens[token] = scope


class APIVersionManager:
    def __init__(self) -> None:
        self._versions: Dict[str, str] = {}
        self._lock = RLock()

    def register_version(self, route_id: str, version: str) -> None:
        with self._lock:
            self._versions[route_id] = version


class APIRateLimiter:
    def __init__(self) -> None:
        self._limits: Dict[str, int] = {}
        self._lock = RLock()

    def set_limit(self, key: str, limit: int) -> None:
        with self._lock:
            self._limits[key] = limit
