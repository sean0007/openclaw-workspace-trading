import os
import threading
import json
import secrets

class VaultStub:
    """In-memory Vault-like stub for tests and CI.

    Stores secrets in a JSON file when a path is provided, otherwise in-memory.
    """
    def __init__(self, path=None):
        self._lock = threading.Lock()
        self._path = path
        if path and os.path.exists(path):
            try:
                with open(path, "r") as f:
                    self._store = json.load(f)
            except Exception:
                self._store = {}
        else:
            self._store = {}

    def get(self, key: str):
        with self._lock:
            val = self._store.get(key)
            if val is None:
                raise KeyError(key)
            return val

    def set(self, key: str, value: str):
        with self._lock:
            self._store[key] = value
            if self._path:
                with open(self._path, "w") as f:
                    json.dump(self._store, f)

    def rotate(self, key: str):
        newval = secrets.token_urlsafe(32)
        self.set(key, newval)
        return newval


class VaultSecretsManager:
    """Facade for a Vault-like backend. Uses VaultStub when VAULT_ADDR is not provided.

    Production setups should set VAULT_ADDR and provide an actual Vault client.
    """

    def __init__(self, path=None):
        # If VAULT_ADDR not set, use stub stored at provided path
        self.vault_addr = os.getenv("VAULT_ADDR")
        if not self.vault_addr:
            self._vault = VaultStub(path)
        else:
            # For environments with hvac installed and Vault available, attempt to use it.
            try:
                import hvac

                client = hvac.Client(url=self.vault_addr)
                token = os.getenv("VAULT_TOKEN")
                if token:
                    client.token = token
                self._vault = client
            except Exception:
                # Fallback to stub if hvac missing or client creation fails
                self._vault = VaultStub(path)

    def get_secret(self, key: str) -> bytes:
        if hasattr(self._vault, "read"):
            # hvac client
            secret = self._vault.read(f"secret/data/{key}")
            if not secret:
                raise KeyError(key)
            # hvac returns nested structure
            data = secret.get("data", {}).get("data", {})
            val = data.get("value")
            if val is None:
                raise KeyError(key)
            return val.encode()
        else:
            # stub
            val = self._vault.get(key)
            if isinstance(val, str):
                return val.encode()
            return val

    def set_secret(self, key: str, value: str):
        if hasattr(self._vault, "write"):
            self._vault.write(f"secret/data/{key}", data={"value": value})
        else:
            self._vault.set(key, value)

    def rotate_secret(self, key: str) -> str:
        if hasattr(self._vault, "write"):
            # For real Vault, generate a random value and write
            newval = secrets.token_urlsafe(32)
            self.set_secret(key, newval)
            return newval
        else:
            return self._vault.rotate(key)
import os


class VaultAdapter:
    def __init__(self, url=None, token=None):
        self.url = url or os.environ.get("VAULT_ADDR")
        self.token = token or os.environ.get("VAULT_TOKEN")

    def get_secret(self, path):
        # stubbed: in CI use file backend; this adapter only validates config
        if not self.url or not self.token:
            raise RuntimeError("Vault not configured")
        return {"key": "vault-secret-placeholder"}
