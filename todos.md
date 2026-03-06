# Todos (derived from MASTER_TRADING_DESK_PLAN)

- [x] Create or restore `todos.md` and populate remaining tasks
- [x] Remediate secret_scan findings (P1-01)
- [x] Add secrets backend integration scaffold (replace stub) (P1-02)
- [x] Debug `execution_service.py`/Signer boot HTTP 403
- [x] Implement remaining P5..P8 artifacts and tests (focus P7/P8)
- [x] Run tests and update `todos.md` with results

All tasks completed: 2026-03-05T07:26:00Z

Audit: verification run completed: 2026-03-05T07:40:00Z

See: [docs/audit_report.md](docs/audit_report.md)

---

Generated: 2026-03-05T00:00:00Z

---

Additional derived tasks (reviewed 2026-03-05T07:50:00Z):

- [ ] Market Data: Implement resilient fallback feed + failover test
      Description: Replace `scripts/p5_*` proof-of-concept stubs with a resilient `market_data.feed_manager` fallback mechanism that automatically fails over between two simulated sources. Add an automated unit/integration test that simulates primary feed loss and verifies continuity and alerting.
      Related Plan Section: Phase 5 - Market Data Pipeline
      Files To Modify: market*data/feed_manager.py, market_data/exchange_ws.py, tests/test_market_data_failover.py, scripts/p5*\* (as needed)
      Acceptance Criteria:
  - `FeedManager` can register two sources and fail over from primary to secondary when primary disconnects
  - Automated test simulates loss and passes within CI
  - An alert artifact is produced when failover occurs

- [ ] Market Data: Add watermarking and freshness checks
      Description: Implement watermark (last-seen timestamps) and freshness validators in `market_data/data_validator.py`. Add unit tests and a dashboard artifact that flags stale data.
      Related Plan Section: Phase 5 - Market Data Pipeline
      Files To Modify: market_data/data_validator.py, tests/test_market_data_freshness.py, scripts/p5_metrics_exporter.py
      Acceptance Criteria:
  - Validator records per-stream watermark timestamps
  - Test verifies detection of stale/cadenced gaps
  - Exported artifact contains watermark summary JSON in `/artifacts/`

- [ ] Execution Safety: DLQ operational handler and replay tool
      Description: Implement a small DLQ processor that reads `artifacts/dlq.db`, exposes an operator endpoint to inspect and replay messages, and a replay tool that re-inserts messages safely with idempotency checks.
      Related Plan Section: DLQ and Retry System
      Files To Modify: scripts/dlq_processor.py, execution_service.py (operator endpoints), nonce_store.py, tests/test_dlq_replay.py
      Acceptance Criteria:
  - DLQ processor can list, inspect, and mark entries replayed
  - Replay tool verifies idempotency and writes to `execution_queue.db` safely
  - Automated test covers replay success and duplicate protection

- [ ] Risk Controls: SAFE MODE validation + automated failover test
      Description: Add a SAFE MODE automated test that triggers a risk kill-switch (via `risk_engine`) and validates that `execution_service` refuses executes and surfaces a clear metric/alert.
      Related Plan Section: SAFE MODE validation, Risk Engine
      Files To Modify: tests/test_safe_mode.py, risk_engine.py, execution_service.py, scripts/alert_rules.py
      Acceptance Criteria:
  - Test can flip kill-switch and observe blocked execution attempts
  - Metric `trading_safe_mode_active` is exported and testable
  - Alert rule artifact created when SAFE MODE engaged

- [ ] State Reconciliation: Scaffold reconciler + reconciliation test
      Description: Create `reconciler/` scaffold that reads execution journals and exchange fills (simulated), verifies positions and PnL, and produces a reconciliation report artifact. Include a unit test to validate mismatch detection.
      Related Plan Section: State Reconciliation
      Files To Modify: reconciler/**init**.py, reconciler/reconciler.py, tests/test_reconciler.py, scripts/p10_reconciliation_runner.py
      Acceptance Criteria:
  - Reconciler can ingest execution journal + market fills and produce report JSON
  - Test detects injected mismatch and fails as expected
  - Reconciliation report stored under `/artifacts/`

- [ ] Strategy Isolation: Add process-based worker + sandboxing test
      Description: Implement a `strategy_worker` that runs strategies in separate processes (multiprocessing) with resource/time limits. Add a test that ensures a strategy crash does not bring down manager and that resource limits enforce termination.
      Related Plan Section: Phase 7 - Strategy Runtime / Isolation
      Files To Modify: strategy_runtime/strategy_worker.py, strategy_runtime/strategy_manager.py, tests/test_strategy_isolation.py
      Acceptance Criteria:
  - Strategy runs in separate process with timeout enforcement
  - Manager continues handling other strategies after crash
  - Test verifies isolation behavior reliably

- [ ] Secrets: Integrate Vault client and rotation test
      Description: Replace the file-backed secrets stub with a pluggable Vault/AWS KMS adapter (config-driven). Add a rotation test that simulates credential rotation and verifies no downtime for `signer_service` and `execution_service`.
      Related Plan Section: Secrets Management (Phase 1)
      Files To Modify: secrets_backend_adapter.py, secrets_backend_vault.py (new), signer_service.py, tests/test_secrets_rotation.py, requirements.txt
      Acceptance Criteria:
  - New Vault adapter can be instantiated via env/config
  - Rotation test simulates rotated secret and services continue with updated secret
  - CI uses file-backend by default; Vault adapter exercised in an integration test

- [ ] Observability: Add metric scrubber tests and exporter improvements
      Description: Add tests ensuring no sensitive keys appear in `/metrics` and extend `scripts/metrics_exporter.py` to scrub known secrets. Produce an artifact that proves metrics are scrubbed.
      Related Plan Section: Observability & Metrics
      Files To Modify: scripts/metrics_exporter.py, execution_service.py, tests/test_metrics_scrub.py
      Acceptance Criteria:
  - Test asserts sensitive substrings are not present in metrics output
  - Exporter scrubs configured secret patterns
  - Artifact generated that demonstrates scrubbed metrics

- [ ] Governance: Immutable off-host audit log stub + retention test
      Description: Add a stub that exports audit logs to an off-host write-once location (simulated S3/local archive) and a retention-check test that validates immutability semantics.
      Related Plan Section: Governance Controls / Audit Logging
      Files To Modify: scripts/audit_exporter.py, tests/test_audit_immutable.py
      Acceptance Criteria:
  - Audit exporter writes timestamped files to `/artifacts/audit/` and marks them immutable (filesystem flag or checksum)
  - Test verifies files cannot be overwritten and retention metadata exists

- [ ] CI/CD: Redact doc phrase, update secret-scan whitelist, CI workflow
      Description: Redact or whitelist the doc phrase that triggers secret-scan in `docs/` and update `.github/workflows/secret_scan.yml` to ignore the specific benign phrase or add a suppression artifact. Add a CI test that runs secret_scan and expects zero high-severity hits.
      Related Plan Section: CI/CD Pipeline / Secrets Scanning
      Files To Modify: docs/audit_report.md (redact), scripts/secret_scan.py, .github/workflows/secret_scan.yml, tests/test_secret_scan_ci.py
      Acceptance Criteria:
  - Secret scan CI job passes with no blocking findings
  - The doc phrase is redacted or explicitly whitelisted in scanner config
  - Test verifies scanner behavior

- [ ] DLQ: Add monitoring and alerting rules for DLQ growth
      Description: Create alert rules and a simple monitor that warns when `dlq.db` growth rate or entry count crosses thresholds. Add unit tests that simulate growth and ensure alerts are emitted as artifacts.
      Related Plan Section: DLQ and Retry System
      Files To Modify: scripts/alert_rules.py, scripts/dlq_monitor.py, tests/test_dlq_alerting.py
      Acceptance Criteria:
  - Monitor can compute growth rate and emit an alert artifact
  - Test triggers alert conditions and validates artifact contents

- [ ] Acceptance: End-to-end smoke harness (30s) with dynamic ports
      Description: Add a `scripts/smoke_harness.py` that launches `signer_service` and `execution_service` on dynamic ports, runs a 30-second simulated workflow (market data feed loss, kill-switch toggle, execution attempts), and produces a pass/fail artifact.
      Related Plan Section: Production Activation / SAFE MODE validation
      Files To Modify: scripts/smoke_harness.py, tests/test_smoke_harness.py
      Acceptance Criteria:
  - Harness runs in CI environment with dynamic ports and completes within ~30s
  - Harness writes `/artifacts/smoke_harness_result.json` with pass/fail and logs
  - Test validates harness success under normal and injected-failure modes

- [ ] Add `MASTER_TRADING_DESK_PLAN.md` to repository or locate canonical path
      Description: Ensure the authoritative `MASTER_TRADING_DESK_PLAN.md` is present in repo root or documented canonical path so automated auditors can read requirements programmatically.
      Related Plan Section: Documentation / Governance
      Files To Modify: MASTER_TRADING_DESK_PLAN.md (new) or update `README.md` with canonical path
      Acceptance Criteria:
  - File `MASTER_TRADING_DESK_PLAN.md` exists at repository root or README references its full path
  - Scripts that reference the file (`scripts/create_baseline.py`) can read it without errors
  - A quick grep for the filename returns a valid path

- [ ] Execution Engine: Add idempotency journal API + unit test
      Description: Expose an operator-only endpoint to query idempotency journal status and add a unit test that verifies idempotency entries are recorded and queried.
      Related Plan Section: Execution Engine / Idempotency
      Files To Modify: execution_service.py, nonce_store.py, tests/test_idempotency_api.py
      Acceptance Criteria:
  - `/operator/idempotency` endpoint returns journal summary JSON
  - Unit test inserts a duplicate execute request and verifies idempotency prevents double-processing
  - Endpoint requires operator API key

- [ ] Execution Engine: Add graceful shutdown and port-reuse test
      Description: Implement a shutdown handler for `execution_service` that cleans up sockets and PID files; add a test that starts/stops the service and rebinds to the same port reliably.
      Related Plan Section: Deployment Safety / Integration Flakiness
      Files To Modify: execution_service.py, tests/test_shutdown_rebind.py
      Acceptance Criteria:
  - Service exposes `/shutdown` operator endpoint or supports SIGTERM gracefully
  - Test starts service on a fixed port, stops it, and restarts on same port without Address in Use errors

- [ ] Secrets: Add CI-friendly file-backend toggle and docs for Vault adapter
      Description: Ensure `secrets_backend_adapter` supports a clear env var to select `file` vs `vault` backends and document usage in README; add a small test that loads file backend in CI.
      Related Plan Section: Secrets Management
      Files To Modify: secrets_backend_adapter.py, README.md, tests/test_secrets_backend_ci.py
      Acceptance Criteria:
  - `SECRETS_BACKEND` env var selects backend with default `file`
  - README contains usage snippet for switching to `vault`
  - CI/unit test covers file-backend behavior

- [ ] Strategy Runtime: Add per-strategy CPU/time limit config test
      Description: Add a small config interface to `strategy_runtime` to set per-strategy timeouts and a unit test that verifies long-running strategy processes are terminated.
      Related Plan Section: Strategy Runtime / Isolation
      Files To Modify: strategy_runtime/strategy_manager.py, tests/test_strategy_timeout.py
      Acceptance Criteria:
  - Manager accepts `strategy_timeout_secs` per strategy
  - Test spawns a strategy that sleeps longer than timeout and is terminated

- [ ] Reconciler: Add exchange-fill ingest adapter (simulated) + unit test
      Description: Add a minimal adapter to `reconciler` that accepts simulated exchange fills (JSON) and ensures reconciler scaffold can parse them.
      Related Plan Section: State Reconciliation
      Files To Modify: reconciler/reconciler.py, tests/test_reconciler_ingest.py
      Acceptance Criteria:
  - Adapter accepts sample fill JSON and returns normalized fill records
  - Unit test asserts normalized fields present (price, qty, timestamp)

- [ ] Observability: Add Prometheus metric name/tag unit test
      Description: Add tests that assert exported Prometheus metrics follow naming conventions and do not include sensitive label values.
      Related Plan Section: Observability & Metrics
      Files To Modify: tests/test_metrics_names.py, scripts/metrics_exporter.py
      Acceptance Criteria:
  - Test verifies metric name prefixes (e.g., `openclaw_` or `trading_`)
  - Test fails if configured sensitive substrings appear in metric labels

- [ ] CI: Add GitHub workflow step to run smoke harness and mark artifacts
      Description: Add a CI job that runs `scripts/smoke_harness.py` with dynamic ports and uploads `/artifacts/smoke_harness_result.json` to job artifacts.
      Related Plan Section: CI/CD Hardening / Production Activation
      Files To Modify: .github/workflows/smoke.yml (new), scripts/smoke_harness.py
      Acceptance Criteria:
  - Workflow runs smoke harness and uploads artifacts on success/failure
  - Workflow set to `workflow_dispatch` and `pull_request` triggers

- [ ] Docs: Add quick-run README section for tests and smoke harness
      Description: Update `README.md` with commands to run unit tests, integration tests, and the smoke harness locally, including env vars and dynamic port tips.
      Related Plan Section: Documentation / Developer UX
      Files To Modify: README.md
      Acceptance Criteria:
  - README contains runnable snippets for `pytest` and `python3 scripts/smoke_harness.py`
  - Instructions include required env vars like `SIGNER_API_KEY` and `EXECUTION_OPERATOR_API_KEY`

-- AUTOGENERATED AUDIT ADDITIONS (appended by repo audit)

ARCHITECTURE

- [ ] Create `core/` scaffold with Strategy/Execution/Risk/MarketData entrypoints
      Description: Add a minimal `core/` package with well-documented entrypoints and boot sequence (init, config load, service registry). This lets agents locate core engines programmatically.
      Files To Modify: core/**init**.py (new), core/boot.py (new), README.md
      Acceptance Criteria:
  - `python -c "import core; core.boot.print_components()"` prints registered engines

- [ ] Add `configs/` canonical config schema and validator
      Description: Create JSON/YAML schema for `openclaw.json` and service configs; add a `scripts/validate_config.py` that validates the live config.
      Files To Modify: configs/schema.yaml (new), scripts/validate_config.py (new)
      Acceptance Criteria:
  - Validator returns non-zero on invalid keys

TRADING ENGINE

- [ ] Implement `strategy_registry` minimal API
      Description: Add `core/strategy_registry.py` to register, list, and load available strategies from `strategies/` directory.
      Files To Modify: core/strategy_registry.py (new), strategies/README.md
      Acceptance Criteria:
  - Agent can call registry to list strategy IDs

- [ ] Wire `market_data.feed_manager` to `market_data/` stubs
      Description: Implement a `FeedManager` that can register sources and failover. Replace `scripts/p5_*` test stubs with calls to the `FeedManager` API.
      Files To Modify: market_data/feed_manager.py (new), scripts/p5_fallback_feed.py
      Acceptance Criteria:
  - `FeedManager` exposes register/start/stop and fails over when primary disconnects

RISK MANAGEMENT

- [ ] Add `risk_engine` API healthcheck and SAFE MODE toggle endpoint
      Description: Expose a simple HTTP operator endpoint (or CLI) to query and toggle SAFE MODE; ensure `execution_service` honors this via the existing risk lock checks.
      Files To Modify: risk_engine.py, execution_service.py
      Acceptance Criteria:
  - `curl -sS -X POST http://127.0.0.1:8000/risk/lock` with operator key toggles risk lock

- [ ] Implement circuit-breaker metric and alert rule
      Description: Export `trading_safe_mode_active` gauge and add `monitoring/alert_rules.py` entry to alert on state changes.
      Files To Modify: risk_engine.py, monitoring/alerting_rules.yml (new)
      Acceptance Criteria:
  - Metric appears via `/metrics` and alert rule file exists

STRATEGY SYSTEM

- [ ] Replace thread-based strategy worker with process-based worker scaffold
      Description: Create `strategy_runtime/strategy_worker.py` process manager that starts strategies in child processes with time/CPU limits.
      Files To Modify: strategy_runtime/strategy_worker.py
      Acceptance Criteria:
  - Test `tests/test_strategy_isolation.py` spawns a sleeping strategy and manager kills it after timeout

- [ ] Add per-strategy config interface for resource limits
      Description: Add YAML per-strategy config schema and loader used by `strategy_manager`.
      Files To Modify: strategy_runtime/config.yaml (new), strategy_runtime/strategy_manager.py
      Acceptance Criteria:
  - Manager reads `strategy_timeout_secs` and enforces it

AGENT AUTOMATION

- [ ] Ensure `agents/` cron wiring exists (or create agent-cron scaffold)
      Description: Create `agents/cron.yml` or ensure OpenClaw agent crons are defined. If absent, add a scaffold so agents are scheduled by OpenClaw cron.
      Files To Modify: agents/cron.yml (new), docs/agents.md (new)
      Acceptance Criteria:
  - Agent cron file lists `main`, `research-lead`, `risk-controller`, etc.

- [ ] Add small todo-agent integration test that executes a single `todos.md` task
      Description: Create an isolated test harness that starts an OpenClaw agent and verifies it picks and executes a trivial task from `todos.md`.
      Files To Modify: tests/test_todo_agent_integration.py
      Acceptance Criteria:
  - Test passes locally and in CI container

MONITORING

- [ ] Add Prometheus scrape config for local services
      Description: Provide `monitoring/prometheus/scrape_configs.yml` with jobs for `execution_service`, `signer_service`, and `strategy_runtime` metrics endpoints.
      Files To Modify: monitoring/prometheus/scrape_configs.yml (new)
      Acceptance Criteria:
  - Prometheus config contains jobs with correct targets (host:port)

- [ ] Implement metrics endpoint in `signer_service` and other services (if missing)
      Description: Verify `/metrics` exists on all core services and implement a small exporter if missing.
      Files To Modify: signer_service.py (update), other services as needed
      Acceptance Criteria:
  - `curl http://127.0.0.1:<port>/metrics` returns Prometheus text

GRAFANA DASHBOARDS

- [ ] Populate `monitoring/grafana/dashboards/trading-desk.json` panels
      Description: Add essential panels for PnL, order latency, fill ratio, market freshness, and strategy queue depth.
      Files To Modify: monitoring/grafana/dashboards/trading-desk.json
      Acceptance Criteria:
  - Dashboard contains at least 5 panels referencing `openclaw_` metrics

- [ ] Add Grafana provisioning validation CI check (grafana-validate.yml)
      Description: Ensure `monitoring/provisioning` files and dashboards validate in CI with `scripts/provision_grafana_dashboards.py`.
      Files To Modify: .github/workflows/grafana-validate.yml (new)
      Acceptance Criteria:
  - CI job validates JSON and fails on secrets

CI/CD

- [ ] Add CI job to run `scripts/smoke_harness.py` and upload artifacts
      Description: Create `.github/workflows/smoke.yml` that runs the smoke harness and saves `/artifacts` outputs.
      Files To Modify: .github/workflows/smoke.yml (new)
      Acceptance Criteria:
  - Workflow runs on PR and `workflow_dispatch`, uploads artifacts

- [ ] Add config validation step in CI (validate_config.py)
      Description: Add a job that runs `scripts/validate_config.py` to catch invalid config keys before merge.
      Files To Modify: .github/workflows/config-validate.yml (new), scripts/validate_config.py
      Acceptance Criteria:
  - PRs with invalid `openclaw.json` fail validation

LOGGING

- [ ] Centralize audit export to `/artifacts/audit/` and add immutability test
      Description: Ensure `scripts/audit_exporter.py` writes immutable audit artifacts and add a test verifying immutability semantics.
      Files To Modify: scripts/audit_exporter.py, tests/test_audit_immutable.py
      Acceptance Criteria:
  - Exporter writes files to `/artifacts/audit/` and test confirms checksum recorded

TESTING

- [ ] Add unit tests for `market_data.feed_manager` failover behavior
      Description: Create `tests/test_market_data_failover.py` that simulates primary disconnect and expects feed manager to switch to secondary.
      Files To Modify: tests/test_market_data_failover.py
      Acceptance Criteria:
  - Test asserts feed manager switched sources and produced fallback artifact

- [ ] Add integration test for reconciler ingest + mismatch detection
      Description: Add `tests/test_reconciler.py` to exercise reconciler with simulated fills and detect injected mismatch.
      Files To Modify: tests/test_reconciler.py
      Acceptance Criteria:
  - Test fails when reconciler detects mismatch

DOCUMENTATION

- [ ] Add `MASTER_TRADING_DESK_PLAN.md` canonical plan (expand placeholder)
      Description: Replace placeholder `MASTER_TRADING_DESK_PLAN.md` with full architecture and acceptance criteria.
      Files To Modify: MASTER_TRADING_DESK_PLAN.md
      Acceptance Criteria:
  - File contains master plan sections referenced by other tasks

- [ ] Add developer runbook for local Grafana/Prometheus setup
      Description: Provide `docs/runbooks/local_monitoring.md` with docker-compose snippets to run Prometheus+Grafana and mount dashboards.
      Files To Modify: docs/runbooks/local_monitoring.md (new)
      Acceptance Criteria:
  - Runbook spins up services with `docker-compose up -d` and dashboards render

---

# AUTOGENERATED: Additional Audit Tasks (scanned 2026-03-06)

The following tasks were appended by the automated architecture audit to cover missing or incomplete items discovered across the repository. Tasks are small, actionable, and agent-executable.

**ARCHITECTURE**

- [ ] Add a canonical `configs/openclaw.schema.yaml` and a lightweight validator script
      Description: Provide a minimal JSON/YAML schema for `openclaw.json` and `configs/validate_config.py` that returns non-zero on schema violations.
      Files To Modify: configs/openclaw.schema.yaml (new), scripts/validate_config.py (new)
      Acceptance Criteria: `python3 scripts/validate_config.py ~/.openclaw/openclaw.json` exits 0 on valid config

- [ ] Create `core/boot.py` service registry and health-check endpoint
      Description: Add a small `core.boot` that registers engine instances and exposes `core.boot.health()` for agents to probe readiness.
      Files To Modify: core/boot.py (new), core/**init**.py (new)
      Acceptance Criteria: `python -c "import core; print(core.boot.health())"` prints JSON

**TRADING ENGINE**

- [ ] Implement a minimal `exchange_adapter` for a single exchange simulator
      Description: Add `core/exchange_adapter.py` that implements connect/subscribe/send_order mocks for tests and smoke harness.
      Files To Modify: core/exchange_adapter.py (new), scripts/exchange_sim.py (new)
      Acceptance Criteria: Smoke harness can place an order against the simulator and receive a simulated fill

- [ ] Add `position_store` API and simple tracking endpoints
      Description: Implement a lightweight position DB and `/operator/positions` read endpoint for audits.
      Files To Modify: execution_service.py (operator endpoint), core/position_store.py (new)
      Acceptance Criteria: POSTing a simulated fill updates positions and GET returns current positions JSON

**RISK MANAGEMENT**

- [ ] Add risk limit config loader and an enforceable check in `execution_service`
      Description: Load per-strategy hard limits from `configs/risk_limits.yaml` and reject executes that exceed limits.
      Files To Modify: configs/risk_limits.yaml (new), risk_engine.py, execution_service.py
      Acceptance Criteria: Test triggers a limit and observe execute rejection with clear error

- [ ] Export `trading_safe_mode_active` metric and add simple alert rule file
      Description: Ensure risk_engine exports the gauge and add `monitoring/alert_rules/trading_safe_mode.yml`.
      Files To Modify: risk_engine.py, monitoring/alert_rules/trading_safe_mode.yml (new)
      Acceptance Criteria: `/metrics` contains `trading_safe_mode_active` and alert rule exists

**STRATEGY SYSTEM**

- [ ] Replace `StrategyWorker` run path with process-based runner (scaffold)
      Description: Update `strategy_runtime/strategy_worker.py` to use multiprocessing for executing strategy callables with a timeout wrapper.

---

APPENDIX: Missing/Incomplete Tasks (automated audit additions 2026-03-06)

ARCHITECTURE

- [ ] Add canonical `docs/master_plan.md` (canonical master plan)
      Description: Populate a single authoritative master plan file (architecture, phases, acceptance criteria) so automated checks can reference it.
      Files To Modify: docs/master_plan.md (new)
      Acceptance Criteria: `tests/e2e/test_master_plan_present.py` passes by finding the file

- [ ] Add `configs/` top-level folder and example `openclaw.json` template
      Description: Provide canonical service config and sample env-driven example for local dev and CI.
      Files To Modify: configs/example_openclaw.json (new), README.md
      Acceptance Criteria: `scripts/validate_config.py configs/example_openclaw.json` exits 0

TRADING ENGINE

- [ ] Implement `core/exchange_adapter.py` simulator adapter
      Description: Small adapter for simulator exchange used by smoke harness and unit tests.
      Files To Modify: core/exchange_adapter.py (new), scripts/exchange_sim.py (new)
      Acceptance Criteria: Smoke harness posts an order and receives a simulated fill

- [ ] Add `/operator/positions` read endpoint to `execution_service`
      Description: Expose current position snapshot for audits and reconciler ingestion.
      Files To Modify: execution_service.py, core/position_store.py (new)
      Acceptance Criteria: `curl /operator/positions` returns JSON with positions

RISK MANAGEMENT

- [ ] Wire `RISK_CIRCUIT_SHARED_SECRET` usage into CI test helper and docs
      Description: Document and make tests use a test shared secret where needed to exercise risk notify endpoints.
      Files To Modify: tests/conftest.py, README.md
      Acceptance Criteria: Risk-notify integration tests run without manual env setup

- [ ] Emit `trading_safe_mode_active` gauge in `risk_engine` and surface in `/metrics`
      Description: Export a gauge and ensure `execution_service` metrics include it for alerting.
      Files To Modify: risk_engine.py, execution_service.py
      Acceptance Criteria: `curl /metrics` returns `trading_safe_mode_active` with 0/1

STRATEGY SYSTEM

- [ ] Implement process-based `strategy_runtime/strategy_worker.py` (minimal)
      Description: Replace or complement thread runner with process runner and enforce timeouts.
      Files To Modify: strategy_runtime/strategy_worker.py
      Acceptance Criteria: `tests/test_strategy_isolation.py` verifies timeout enforcement

- [ ] Add per-strategy config loader and examples
      Description: Provide `strategy_runtime/example_strategy.yaml` showing `strategy_timeout_secs` and `max_memory_mb` entries.
      Files To Modify: strategy_runtime/example_strategy.yaml (new), strategy_runtime/strategy_manager.py
      Acceptance Criteria: Manager reads config and applies timeout to worker

AGENT AUTOMATION

- [ ] Add `agents/cron.yml` scaffold and docs for agent scheduling
      Description: Create a simple cron definition for OpenClaw agents (todo-agent, monitoring-agent, arch-agent).
      Files To Modify: agents/cron.yml (new), docs/agents.md (new)
      Acceptance Criteria: `openclaw agent-scheduler validate agents/cron.yml` (or reviewer checks file exists)

- [ ] Add small `tests/test_todo_agent_integration.py` harness
      Description: Start a local OpenClaw agent instance and verify it executes one trivial task from `todos.md`.
      Files To Modify: tests/test_todo_agent_integration.py (new)
      Acceptance Criteria: CI can run the test in isolation

MONITORING

- [ ] Ensure `monitoring/prometheus/scrape_configs.yml` includes all core services
      Description: Add jobs for `execution_service`, `signer_service`, `strategy_service` and `reconciler` with configurable ports.
      Files To Modify: monitoring/prometheus/scrape_configs.yml
      Acceptance Criteria: Prometheus job list contains these jobs

- [ ] Add exporter in `signer_service` if missing and verify scrape target
      Description: Confirm `/metrics` exists and add minimal counters (tokens_issued_total) if absent.
      Files To Modify: signer_service.py
      Acceptance Criteria: `curl /metrics` returns a Prometheus text response with token metric

GRAFANA DASHBOARDS

- [ ] Add required panels to `monitoring/grafana/dashboards/trading-desk.json`
      Description: Ensure panels cover PnL, order latency, fill rate, market freshness, strategy queue depth.
      Files To Modify: monitoring/grafana/dashboards/trading-desk.json
      Acceptance Criteria: Dashboard JSON contains at least five panels referencing `openclaw_` metrics

CI/CD

- [ ] Add `.github/workflows/smoke.yml` to run `scripts/smoke_harness.py` and upload artifacts
      Description: Smoke harness validates system health end-to-end and produces `artifacts/smoke_harness_result.json`.
      Files To Modify: .github/workflows/smoke.yml (new)
      Acceptance Criteria: Workflow runs on PR and uploads artifacts

- [ ] Push `fix/tests-integration` branch to remote and open a PR
      Description: Publish local branch and create a PR for review of test fixes and CI changes.
      Files To Modify: (repo remote)
      Acceptance Criteria: PR exists on remote repository

LOGGING

- [ ] Add `scripts/audit_exporter.py` config to ship audit logs to `/artifacts/audit/`
      Description: Ensure audit export writes append-only files and include a retention metadata JSON.
      Files To Modify: scripts/audit_exporter.py, docs/runbooks/critical_alert_runbook.md
      Acceptance Criteria: Artifacts produced and retention JSON written

TESTING

- [ ] Add unit test coverage target and CI upload for coverage.xml
      Description: Configure `pytest` to generate coverage and upload as artifact in CI.
      Files To Modify: .github/workflows/ci.yml (update), requirements.txt
      Acceptance Criteria: `results/coverage.xml` uploaded as CI artifact

- [ ] Add integration test for reconciler ingest and mismatch detection
      Description: Expand `tests/test_reconciler_ingest.py` to validate reconciler detects mismatches and fails accordingly.
      Files To Modify: tests/test_reconciler_ingest.py
      Acceptance Criteria: Test asserts mismatch detection

DOCUMENTATION

- [ ] Update `docs/audit_report.md` with this audit summary and link to new tasks
      Description: Append a brief summary of missing components and link to `todos.md` sections.
      Files To Modify: docs/audit_report.md
      Acceptance Criteria: File contains summary and links to `todos.md`

      Files To Modify: strategy_runtime/strategy_worker.py
      Acceptance Criteria: `tests/test_strategy_isolation.py` spawns a sleeping strategy which is killed after timeout

- [ ] Add `strategies/README.md` and a sample concrete strategy implementation
      Description: Add one example strategy class (`strategies/example_strategy.py`) that the registry can load.
      Files To Modify: strategies/example_strategy.py (new), strategies/README.md (new)
      Acceptance Criteria: `core.strategy_registry` can load `example_strategy` and return its ID

**AGENT AUTOMATION**

- [ ] Add `agents/cron.yml` scaffold and register basic agent tasks
      Description: Create an OpenClaw-compatible `agents/cron.yml` that schedules the `todo-agent` and `monitoring-agent` every 5m.
      Files To Modify: agents/cron.yml (new), docs/agents.md (new)
      Acceptance Criteria: OpenClaw agent list includes cron entries and agents can be started by name

- [ ] Create `tests/test_todo_agent_integration.py` that verifies a single `todos.md` task completes
      Description: Start an OpenClaw agent in test harness and verify it consumes and marks one trivial task from `todos.md` as done.
      Files To Modify: tests/test_todo_agent_integration.py (new)
      Acceptance Criteria: CI-local test passes and artifacts/log show task execution

**MONITORING**

- [ ] Add Prometheus service monitor for the reconciler and DLQ processors
      Description: Update `monitoring/prometheus/scrape_configs.yml` to include reconciler and dlq monitor ports.
      Files To Modify: monitoring/prometheus/scrape_configs.yml
      Acceptance Criteria: `curl` to each configured `/metrics` endpoint returns Prometheus text

- [ ] Implement a small `/metrics` endpoint for reconciler (scaffold)
      Description: Add a minimal metrics endpoint to `reconciler/reconciler.py` exposing reconciliation counters.
      Files To Modify: reconciler/reconciler.py
      Acceptance Criteria: `curl http://127.0.0.1:<port>/metrics` returns reconciliation metric lines

**GRAFANA DASHBOARDS**

- [ ] Add panel templates referencing `openclaw_signer_tokens_issued_total` and `openclaw_execution_*` metrics
      Description: Populate `monitoring/grafana/dashboards/trading-desk.json` with templated panels for tokens, fills, and queue depth.
      Files To Modify: monitoring/grafana/dashboards/trading-desk.json
      Acceptance Criteria: Dashboard JSON includes at least these metric queries

- [ ] Add dashboard provisioning CI check (use `scripts/provision_grafana_dashboards.py`)
      Description: Create `.github/workflows/grafana-validate.yml` to run the provision script and fail on invalid JSON.
      Files To Modify: .github/workflows/grafana-validate.yml (new)
      Acceptance Criteria: Workflow validates dashboards on PRs

**CI/CD**

- [ ] Add CI job to run `scripts/validate_config.py` and `pytest` in parallel
      Description: Add `.github/workflows/ci.yml` step that validates config schema and runs tests; fail on linter or schema errors.
      Files To Modify: .github/workflows/ci.yml (update)
      Acceptance Criteria: PRs run validation and tests; failure blocks merge

- [ ] Add CI artifact upload for `/artifacts` after smoke harness
      Description: Extend smoke workflow to upload the `artifacts/` folder into job artifacts for review.
      Files To Modify: .github/workflows/smoke.yml
      Acceptance Criteria: Artifacts available from CI job UI after run

**LOGGING**

- [ ] Add `scripts/audit_exporter.py` to copy recent audit lines to `/artifacts/audit/` with checksum
      Description: Export the last 24h of audit events into a timestamped file and write a checksum for provenance.
      Files To Modify: scripts/audit_exporter.py (new)
      Acceptance Criteria: Running script produces `/artifacts/audit/<ts>.json` and `<ts>.sha256`

**TESTING**

- [ ] Add unit tests verifying Prometheus metric names and absence of secrets
      Description: `tests/test_metrics_names.py` should assert metric name prefixes and scan for secret patterns.
      Files To Modify: tests/test_metrics_names.py (new)
      Acceptance Criteria: Test fails if metric names or labels contain disallowed patterns

- [ ] Add `tests/test_reconciler_ingest.py` for reconciler fill normalization
      Description: Provide a minimal unit test that feeds sample fills to reconciler adapter and asserts normalized values.
      Files To Modify: tests/test_reconciler_ingest.py (new)
      Acceptance Criteria: Test passes with adapter implementation

**DOCUMENTATION**

- [ ] Expand `MASTER_TRADING_DESK_PLAN.md` with acceptance criteria and component responsibilities
      Description: Replace the placeholder plan with concrete milestones, owners, and testable acceptance criteria.
      Files To Modify: MASTER_TRADING_DESK_PLAN.md
      Acceptance Criteria: Master plan references the tasks above and is parsable by agents

- [ ] Add `docs/runbooks/local_monitoring.md` with quick start for Grafana/Prometheus
      Description: Provide `docker-compose` snippet and instructions to mount `monitoring/grafana/dashboards` for local dev.
      Files To Modify: docs/runbooks/local_monitoring.md (new)
      Acceptance Criteria: Developers can run monitoring locally with provided commands
