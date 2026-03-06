# Alert Rules

This folder contains Prometheus alerting rules for the trading system. Key files:

- `trading_safe_mode.yml`: Alerts for execution rejections, DLQ growth, feed failover, gateway safe mode, signer token rates, and node exporter availability.

How to validate locally:

1. Install Prometheus or use Docker image `prom/prometheus:latest`.
2. Use `promtool` (bundled in the Docker image) to validate rules:

```bash
docker run --rm -v $(pwd)/monitoring/alert_rules:/etc/prometheus/rules:ro prom/prometheus:latest promtool check rules /etc/prometheus/rules
```

3. Validate Prometheus config (if needed):

```bash
docker run --rm -v $(pwd)/monitoring/prometheus:/etc/prometheus:ro prom/prometheus:latest promtool check config /etc/prometheus/prometheus.yml
```

Notes:

- Alerts use operational metric names exported by `execution_service` and `signer_service`.
- Tune thresholds and durations (`for:`) to match production characteristics before enabling paging.
