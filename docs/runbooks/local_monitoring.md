# Local Monitoring Runbook

This runbook shows how to run Prometheus and Grafana locally and ensure Grafana loads dashboards from the repository so they persist.

Prerequisites:

- Docker and docker-compose installed.
- Ports 3000 (Grafana) and 9090 (Prometheus) available.

From repository root:

1. Start services (uses `docker-compose.yml` in repository):

```bash
docker-compose up -d prometheus grafana
```

2. Verify services are running:

```bash
curl -sS http://localhost:9090/graph | head -n1 && echo Prometheus
curl -sS -u admin:adminMe1977! http://localhost:3000/api/health | jq .
```

3. Verify dashboards are provisioned (Grafana admin credentials from `docker-compose.yml`):

```bash
curl -sS -u admin:adminMe1977! 'http://localhost:3000/api/search?query=&type=dash-db' | jq .
```

Notes:

- The repository mounts `monitoring/grafana/dashboards` into the container at `/var/lib/grafana/dashboards` via `docker-compose.yml`. Keep dashboards there so they are version-controlled and persist.
- Prometheus config is `monitoring/prometheus/scrape_configs.yml` and is mounted as `/etc/prometheus/prometheus.yml`.
- If Grafana dashboards are deleted in the UI, provisioning with `disableDeletion: true` will prevent provisioning from removing them; dashboards are marked non-editable in repo JSONs to avoid accidental changes.

If any metrics are missing, add exporter endpoints in the services and include them in `monitoring/prometheus/scrape_configs.yml`.
