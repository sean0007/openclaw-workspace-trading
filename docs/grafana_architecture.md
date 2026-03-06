# Grafana Architecture — OpenClaw Trading Desk

Overview

This document describes how Grafana dashboards are provisioned for the OpenClaw trading desk, how agents and services expose metrics, and the safe editing and deployment workflow.

Provisioning

- Dashboards live in the repository under `monitoring/grafana/dashboards/` as JSON files. Grafana is configured to load dashboards from `/var/lib/grafana/dashboards` using provisioning files in `monitoring/grafana/provisioning/`.
- `monitoring/grafana/provisioning/dashboards.yml` declares a provider named `TradingDesk` which points Grafana at `/var/lib/grafana/dashboards` inside the Grafana runtime. Use container mounts or a symbolic link to ensure the repository folder (or a copy) is available at that path in the Grafana container.
- `monitoring/grafana/provisioning/datasources.yml` provides datasource configuration. The provisioning file references environment variables (e.g. `${PROMETHEUS_URL}`) — set them at container startup or via your orchestration system so Grafana reads credentials from the environment, not from checked-in files.

Dashboard format and constraints

- Dashboards must be stored as standalone JSON files. Do not rely on Grafana's internal DB for the canonical dashboard source.
- Dashboards must not contain embedded secrets (no `secureJsonData`, `password`, `api_key`, `token`, or `secret` fields).

Agents and metrics

- OpenClaw agents and services should expose Prometheus-format metrics on `/metrics` endpoints. Example metric names used by dashboards:
  - `openclaw_pnl_total`, `openclaw_pnl_realized`, `openclaw_pnl_unrealized`
  - `openclaw_order_latency_bucket`, `openclaw_fill_ratio`, `openclaw_slippage_bps`
  - `openclaw_market_price`, `openclaw_market_spread`, `openclaw_market_volume`
  - `openclaw_strategy_latency_ms`, `openclaw_worker_queue_depth`, `openclaw_api_latency_ms`
- Dashboards query the configured Prometheus datasource. Ensure the datasource URL is reachable from within the Grafana container (use `host.docker.internal` for local Docker on macOS, or appropriate service names in k8s).

Editing workflow

1. Export or edit dashboards locally using the `scripts/export_grafana_dashboard.sh` script. This pulls the dashboard JSON by UID from a running Grafana and saves it to `monitoring/grafana/dashboards/`.

2. Edit the JSON in the repository. Prefer small, reviewed diffs. Avoid changing datasource credentials inside the JSON.

3. Open a PR. The CI workflow `.github/workflows/grafana-validate.yml` validates JSON, detects accidental secrets, and ensures provisioning files exist.

Deployment

- In containerized deployments, mount `$(pwd)/monitoring/grafana/dashboards` to `/var/lib/grafana/dashboards` in the Grafana container. For example:

```sh
docker run -d --name=grafana \
  -e PROMETHEUS_URL=http://prometheus:9090 \
  -v $(pwd)/monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro \
  -v grafana-data:/var/lib/grafana \
  grafana/grafana:latest
```

- On systems where mounts are not possible, use a CI job to push dashboard JSON to Grafana via the HTTP API at deploy-time.

Verification

- After Grafana restart, dashboards listed under the `Trading Desk` folder should appear automatically.
- Confirm that panels show metrics by checking Prometheus queries directly or looking at panel inspection.

Security

- Never commit credentials in dashboards. Use environment variables or secrets management for datasource credentials.
- Dashboards are read-only in the repository; editing should happen via PRs.

Support

If a dashboard fails to render due to missing metrics, verify the metric name and the Prometheus scrape configuration. For more complex provisioning (multiple orgs/folders), extend `provisioning/dashboards.yml` with additional providers.
