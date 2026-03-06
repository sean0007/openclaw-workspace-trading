#!/usr/bin/env bash
set -euo pipefail

# Exports a Grafana dashboard to the repository dashboards folder by UID
# Required env vars: GRAFANA_URL, GRAFANA_ADMIN_USER, GRAFANA_ADMIN_PASS
# Usage: ./scripts/export_grafana_dashboard.sh <dashboard-uid> [out-file]

GRAFANA_URL=${GRAFANA_URL:-http://localhost:3000}
USER=${GRAFANA_ADMIN_USER:-admin}
PASS=${GRAFANA_ADMIN_PASS:-}
if [ -z "$PASS" ]; then
  echo "GRAFANA_ADMIN_PASS is required" >&2
  exit 2
fi

UID=$1
OUT=${2:-monitoring/grafana/dashboards/${UID}.json}

echo "Exporting dashboard UID=$UID to $OUT"
mkdir -p "$(dirname "$OUT")"

curl -sS -u "$USER:$PASS" "$GRAFANA_URL/api/dashboards/uid/$UID" \
  | jq '.dashboard' > "$OUT"

# Basic validation
if ! jq empty "$OUT" >/dev/null 2>&1; then
  echo "Export produced invalid JSON" >&2
  exit 3
fi

echo "Saved: $OUT"
