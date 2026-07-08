from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from threading import RLock
from typing import Any


class ProviderKeyManager:
    """Secure key manager with masked display, validation, rotation, and encrypted storage."""

    def __init__(self, storage_path: str | None = None) -> None:
        self._storage_path = Path(storage_path or "/tmp/provider-keys.json")
        self._audit_path = self._storage_path.with_suffix(".audit.jsonl")
        self._lock = RLock()
        self._keys: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self._storage_path.exists():
            return
        try:
            with self._storage_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
                self._keys = {str(k): str(v) for k, v in payload.items()}
        except Exception:
            self._keys = {}

    def _persist(self) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self._storage_path.open("w", encoding="utf-8") as handle:
            json.dump(self._encrypt_payload(self._keys), handle)

    def _encrypt_payload(self, payload: dict[str, str]) -> dict[str, str]:
        key = os.environ.get("TANGKU_PROVIDER_KEY", "tangku-provider-hub").encode("utf-8")
        encrypted: dict[str, str] = {}
        for provider_id, value in payload.items():
            encoded = value.encode("utf-8")
            masked = bytes(b ^ key[index % len(key)] for index, b in enumerate(encoded))
            encrypted[provider_id] = base64.b64encode(masked).decode("utf-8")
        return encrypted

    def _decrypt_payload(self, payload: dict[str, str]) -> dict[str, str]:
        key = os.environ.get("TANGKU_PROVIDER_KEY", "tangku-provider-hub").encode("utf-8")
        decrypted: dict[str, str] = {}
        for provider_id, value in payload.items():
            try:
                raw = base64.b64decode(value.encode("utf-8"))
                text = bytes(b ^ key[index % len(key)] for index, b in enumerate(raw))
                decrypted[provider_id] = text.decode("utf-8")
            except Exception:
                decrypted[provider_id] = ""
        return decrypted

    def _audit(self, action: str, provider_id: str, success: bool) -> None:
        self._audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self._audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"action": action, "provider_id": provider_id, "success": success}) + "\n")

    def save_key(self, provider_id: str, value: str) -> str:
        with self._lock:
            if not self.validate_key(value):
                raise ValueError("provider key must not be empty")
            self._keys[provider_id] = value
            self._persist()
            self._audit("save", provider_id, True)
            return value

    def get_key(self, provider_id: str) -> str | None:
        with self._lock:
            if self._storage_path.exists():
                try:
                    with self._storage_path.open("r", encoding="utf-8") as handle:
                        payload = json.load(handle)
                        self._keys = self._decrypt_payload({str(k): str(v) for k, v in payload.items()})
                except Exception:
                    self._keys = {}
            return self._keys.get(provider_id)

    def remove_key(self, provider_id: str) -> None:
        with self._lock:
            self._keys.pop(provider_id, None)
            self._persist()
            self._audit("remove", provider_id, True)

    def rotate_key(self, provider_id: str, value: str) -> str:
        return self.save_key(provider_id, value)

    def validate_key(self, value: str | None) -> bool:
        return bool(value and str(value).strip())

    def mask_value(self, value: str | None) -> str:
        if not value:
            return ""
        return "***"

    def masked_value(self, provider_id: str) -> str:
        with self._lock:
            env_key = os.environ.get(f"TANGKU_PROVIDER_{provider_id.upper()}_KEY") or os.environ.get("TANGKU_PROVIDER_OPENAI_KEY")
            if env_key:
                return "***"
            return self.mask_value(self._keys.get(provider_id))

    def export_keys(self) -> dict[str, str]:
        with self._lock:
            exported: dict[str, str] = {}
            for provider_id in self._keys:
                exported[provider_id] = "***"
            env_provider = os.environ.get("TANGKU_PROVIDER_OPENAI_KEY")
            if env_provider:
                exported.setdefault("openai", "***")
            return exported

    def export_encrypted(self) -> dict[str, str]:
        with self._lock:
            return self._encrypt_payload(self._keys)

    def import_keys(self, payload: dict[str, str]) -> None:
        with self._lock:
            self._keys.update({str(k): str(v) for k, v in payload.items()})
            self._persist()
            self._audit("import", "multiple", True)

    def resolve_value(self, provider_id: str) -> str | None:
        with self._lock:
            env_key = os.environ.get(f"TANGKU_PROVIDER_{provider_id.upper()}_KEY") or os.environ.get("TANGKU_PROVIDER_OPENAI_KEY")
            if env_key:
                return env_key
            return self._keys.get(provider_id)
