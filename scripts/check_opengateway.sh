#!/usr/bin/env bash
set -euo pipefail

# Check OpenClaw execution gateway endpoints and basic metrics
EXEC_URL=${EXEC_SERVICE_URL:-http://127.0.0.1:8000}
TIMEOUT=3

echo "Checking execution gateway at $EXEC_URL"

# /state
if curl -sS -m ${TIMEOUT} "$EXEC_URL/state" -o /tmp/_state.json; then
  echo "- /state: OK"
  jq -r '. | keys' /tmp/_state.json || true
else
  echo "- /state: FAILED to reach $EXEC_URL/state" >&2
fi

# /metrics
if curl -sS -m ${TIMEOUT} "$EXEC_URL/metrics" -o /tmp/_metrics.txt; then
  echo "- /metrics: OK"
  # check expected metrics
  for m in openclaw_execution_gateway_boot_completed openclaw_execution_gateway_risk_locked openclaw_execute_requests_total; do
    if grep -q "$m" /tmp/_metrics.txt; then
      echo "  - metric $m: present"
    else
      echo "  - metric $m: MISSING"
    fi
  done
else
  echo "- /metrics: FAILED to reach $EXEC_URL/metrics" >&2
fi

# quick DB path check (if running locally)
DB_PATH=${EXECUTION_SERVICE_DB:-/tmp/execution_service_nonce.db}
if [ -f "$DB_PATH" ]; then
  echo "- DB path $DB_PATH: file exists"
else
  echo "- DB path $DB_PATH: not found"
fi

echo "Check complete."
