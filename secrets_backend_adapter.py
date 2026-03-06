"""Secrets backend adapter scaffold.

Provides a minimal adapter interface and local file backend plus placeholders
for Vault/AWS/other providers to make integration straightforward.
"""
import os
import json

class BaseSecretsBackend:
    """Abstract base for secrets backends."""
    def get(self, key, default=None):
        raise NotImplementedError()

    def set(self, key, value):
        raise NotImplementedError()


class FileSecretsBackend(BaseSecretsBackend):
    def __init__(self, path=None):
        self.path = path or os.environ.get("SECRETS_FILE_PATH")
        self._data = {}
        if self.path and os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}

    def get(self, key, default=None):
        if key in self._data:
            return self._data[key]
        return os.environ.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        if self.path:
            with open(self.path, "w") as f:
                json.dump(self._data, f)


class VaultBackend(BaseSecretsBackend):
    """Placeholder for HashiCorp Vault integration.

    Implement `__init__(url, token)` and the `get`/`set` methods using
    the chosen Vault client (hvac) or HTTP API. This scaffold keeps tests
    and local development using `FileSecretsBackend` while enabling
    straightforward integration later.
    """
    def __init__(self, url=None, token=None):
        raise NotImplementedError("VaultBackend not implemented in scaffold")


def get_backend(kind=None, **kwargs):
    kind = kind or os.environ.get("SECRETS_BACKEND_KIND", "file")
    if kind == "file":
        return FileSecretsBackend(kwargs.get("path"))
    if kind == "vault":
        return VaultBackend(kwargs.get("url"), kwargs.get("token"))
    raise ValueError("unknown secrets backend kind")
