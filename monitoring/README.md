Monitoring stack (local dev)

This folder contains local monitoring helpers and an Alertmanager webhook receiver used
for local testing.

Quick start (uses docker-compose):

- Start stack (Prometheus/Grafana/Alertmanager/receiver/MailHog):

```bash
cd /path/to/openclaw-workspace-trading
docker-compose up -d prometheus grafana alertmanager alert-receiver mailhog node-exporter
```

- Send a test alert to Alertmanager v2 API:

```bash
curl -XPOST -H "Content-Type: application/json" http://localhost:9094/api/v2/alerts -d '[{"labels":{"alertname":"SmokeTest","severity":"info"},"annotations":{"summary":"smoke test"},"startsAt":"2026-03-06T00:00:00Z","endsAt":"2026-03-06T00:05:00Z"}]'
```

- Check receiver persisted alerts:

```bash
ls -la monitoring/alertmanager/data
cat monitoring/alertmanager/data/alertmanager_received.jsonl
```

- Check MailHog UI for captured emails: http://localhost:8025

Notes:
- The receiver writes to `monitoring/alertmanager/data/alertmanager_received.jsonl`.
- The `docker-compose.yml` mounts `monitoring/alertmanager/config.yml` into the container.
