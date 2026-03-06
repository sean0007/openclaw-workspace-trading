"""
Minimal stub secrets backend for local testing. Provides a get_secret(name) API and reads from a file or env.
"""
import os
import json

class FileSecretsBackend:
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
        # fallback to env
        if key in self._data:
            return self._data[key]
        return os.environ.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        if self.path:
            with open(self.path, "w") as f:
                json.dump(self._data, f)

def get_default_backend():
    return FileSecretsBackend()
