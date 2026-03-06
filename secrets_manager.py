import os
import json
import threading


class SecretsManagerError(Exception):
    pass


class SecretsManager:
    """Abstract secrets manager interface.

    Production: implement HashiCorp Vault or cloud KMS here.
    For tests/local: use FileSecretsManager.
    """

    def get_secret(self, key: str) -> bytes:
        raise NotImplementedError()


class FileSecretsManager(SecretsManager):
    """Simple file-backed secrets manager. Stores JSON map at path.

    This is only for local testing. Do NOT use in production.
    """

    def __init__(self, path=None):
        self.path = path or os.getenv("SECRETS_FILE_PATH", "/tmp/secrets.json")
        self._lock = threading.Lock()
        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                json.dump({}, f)

    def _read(self):
        with open(self.path, "r") as f:
            raw = f.read().strip()
            if not raw:
                return {}
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                raise SecretsManagerError(f"invalid secrets file format: {self.path}") from exc

    def get_secret(self, key: str) -> bytes:
        with self._lock:
            data = self._read()
            if key not in data:
                raise SecretsManagerError(f"secret {key} not found")
            val = data[key]
            if isinstance(val, str):
                return val.encode()
            return val

    def set_secret(self, key: str, value: str):
        with self._lock:
            data = self._read()
            data[key] = value
            with open(self.path, "w") as f:
                json.dump(data, f)


def get_secrets_manager(path=None):
    """Factory: choose secrets backend via `SECRETS_BACKEND` env var.

    Supported values: `file` (default), `vault`, `stub`.
    """
    backend = os.getenv("SECRETS_BACKEND", "file").lower()
    if backend == "file":
        return FileSecretsManager(path)
    if backend in ("vault", "stub"):
        try:
            from secrets_backend_vault import VaultSecretsManager

            return VaultSecretsManager(path)
        except Exception:
            # fallback to file-backed manager
            return FileSecretsManager(path)
    # default
    return FileSecretsManager(path)


def rotate_secret(key: str, manager=None):
    """Rotate a secret using the provided manager or the factory.

    Returns the new secret string.
    """
    mgr = manager or get_secrets_manager()
    if hasattr(mgr, "rotate_secret"):
        return mgr.rotate_secret(key)
    # best-effort fallback: generate and set
    newval = secrets.token_urlsafe(32)
    if hasattr(mgr, "set_secret"):
        mgr.set_secret(key, newval)
    return newval
