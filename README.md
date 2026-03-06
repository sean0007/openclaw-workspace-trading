RiskEngine scaffold

This folder contains a minimal RiskEngine + ExecutionEngine scaffold and unit tests.

Run tests:

```bash
python3 -m pip install -r requirements.txt
pytest -q
```

Notes:

- `RISK_EXECUTOR_SHARED_SECRET` environment variable must be set; tests set it via pytest fixture.
- This scaffold is designed to demonstrate enforcement: fail-closed, HMAC-signed execution tokens, JSON logging.

Quick-run smoke harness

```bash
python3 scripts/smoke_harness.py
```

Required env vars for integration tests:

- `SIGNER_API_KEY` - API key for signer tests
- `EXECUTION_OPERATOR_API_KEY` - operator key for execution service
