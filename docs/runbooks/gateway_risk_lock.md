# Gateway Risk Lock

Symptoms:

- `GatewayRiskLocked` alert firing.

Immediate actions:

- Check `risk_engine.py` logs for reasons the lock engaged.
- Confirm operator actions required to clear the lock.

Notes:

- Only clear lock after confirming system safety and manual approval.
