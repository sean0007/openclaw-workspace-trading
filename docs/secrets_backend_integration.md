Secrets backend integration scaffold

This document describes how to replace the local file-based secrets stub with
an enterprise secrets manager (HashiCorp Vault, AWS Secrets Manager, etc.).

Recommended approach:

- Use `secrets_backend_adapter.get_backend(kind="vault", url=..., token=...)`
  to obtain a `BaseSecretsBackend` instance.
- Implement a `VaultBackend` class using the `hvac` client and provide `get` and
  `set` methods. Use environment variables or instance metadata for token
  retrieval in production.
- Keep a `FileSecretsBackend` for local development and CI to avoid external
  network calls.

Local dev example:

- Set `SECRETS_FILE_PATH` to a temp JSON file and `SECRETS_BACKEND_KIND=file`.
- The application should call `get_backend()` once at startup and use the
  returned object for secret access.

Security notes:

- Never commit real secrets to the repository. Use the `secret_scan.py` tool
  to detect accidental leakages.
- Rotate credentials when moving from file-based dev secrets to production
  secret managers.
