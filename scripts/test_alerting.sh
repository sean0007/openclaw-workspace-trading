#!/usr/bin/env bash
set -euo pipefail

# Send a v2 Alertmanager test alert and then query MailHog and receiver file
curl -s -XPOST -H "Content-Type: application/json" http://localhost:9094/api/v2/alerts -d '[{"labels":{"alertname":"CIAlertTest","severity":"critical"},"annotations":{"summary":"ci test"},"startsAt":"2026-03-06T00:00:00Z","endsAt":"2026-03-06T00:05:00Z"}]'

sleep 2

echo "--- receiver file ---"
ls -la monitoring/alertmanager/data || true
sed -n '1,120p' monitoring/alertmanager/data/alertmanager_received.jsonl || true

echo "--- mailhog count ---"
curl -sS http://localhost:8025/api/v2/messages | jq '.total' || true
