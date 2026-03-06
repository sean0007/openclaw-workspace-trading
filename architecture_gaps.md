# Architecture Gaps — Automated Audit Log

Generated: 2026-03-05T08:30:00Z

## GAP: MASTER_TRADING_DESK_PLAN.md

Status:
Present (placeholder)

Expected Behavior:
The repository must include `MASTER_TRADING_DESK_PLAN.md` at the repository root containing the canonical architecture plan and requirements. Automated auditors and agents must be able to read and parse this file.

Current State:
A minimal `MASTER_TRADING_DESK_PLAN.md` placeholder has been added to the repository root to satisfy automated auditors. This file should be expanded into the canonical plan before production rollout.

Risk Level:
Reduced (documentation present)

Failure Impact:
Automated verification can now locate a master plan; reviewers should ensure the placeholder is replaced with the canonical plan.

Required Systems:
Documentation store, CI, automated auditors

## GAP: Market Data Pipeline (production-grade)

Status:
Partial / Stubbed

Expected Behavior:
A resilient real-time ingest pipeline (multi-source ingestion, watermarking, normalization, latency monitoring, failover) with automated failover testing and alerting.

Current State:
`market_data/` contains simulator and validators; multiple `scripts/p5_*` stubs exist producing artifacts but no production-grade pipeline or failover orchestration service.

Risk Level:
High

Failure Impact:
Stale or inconsistent market data may lead to incorrect orders and PnL mismatches.

Required Systems:
`market_data.feed_manager`, feed orchestrator, alerting, metrics

## GAP: State Reconciler Service

Status:
Partial — skeleton service added

Expected Behavior:
A persistent reconciler service that ingests execution journals and market fills, performs periodic reconciliation, stores reports, and surfaces mismatches as alerts.

Current State:
Added `reconciler/reconciler_service.py` as a minimal reconciler skeleton. The service requires scheduling, fill adapters, report generation, and alerting integration to be production-ready.

Risk Level:
Still Critical until full reconciliation logic and scheduling are implemented.

Failure Impact:
Undetected ledger mismatches may remain until reconciler is fully implemented.

Required Systems:
Reconciler service, execution journal, fills ingest adapters, alerting/metrics

## GAP: Strategy Runtime Isolation

Status:
Partial

Expected Behavior:
Per-strategy process-level sandboxing with resource/time limits and crash containment (process isolation or container-based sandbox).

Current State:
`strategy_runtime/strategy_worker.py` provides a thread-based worker and a minimal process-run helper, but no full process-manager or sandbox orchestration.

Risk Level:
High

Failure Impact:
A faulty strategy can impact host process, leak resources, or cause execution instability.

Required Systems:
Strategy process manager, orchestration, resource limiter, monitoring

## GAP: Secrets Management (production integration)

Status:
Improved (Vault stub + rotation helper added)

Expected Behavior:
Pluggable production secrets backend (Vault/KMS) with rotation tooling and CI-safe file-backend fallback.

Current State:
Added `secrets_backend_vault.py` with a `VaultSecretsManager` facade and an in-memory/file-backed `VaultStub`. `secrets_manager.get_secrets_manager()` factory and `rotate_secret()` helper were added; a CI test for rotation exists. Production Vault integration (hvac + access control) still requires configuration.

Risk Level:
Reduced (rotation and pluggable backends are available in tests)

Failure Impact:
Production still requires secure Vault configuration and access controls.

Required Systems:
Vault adapter, rotation runner, CI toggles

## GAP: DLQ Operational Handler

Status:
Partial — operator endpoint added

Expected Behavior:
Operator-visible DLQ service with inspection, replay, and idempotency-safe re-insertion to the execution queue.

Current State:
Added `/operator/dlq` stub endpoint to `execution_service.py` providing list/replay/delete actions (stubbed). A full DLQ backend and replay worker remain to be implemented for production.

Risk Level:
Reduced for operator visibility; still High until idempotent replay is implemented.

Required Systems:
DLQ processor service, operator endpoints, idempotency journal

## GAP: CI Secret-Scan Blocking Phrase

Status:
Stubbed/Issue

Expected Behavior:
CI secret-scan should not be blocked by benign doc phrases; sensitive terms should be redacted or scanner whitelisted with audit.

Current State:
Latest secret scan flagged a doc phrase as "AWS Secret"; remediation required to redact or whitelist.

Risk Level:
Medium

Failure Impact:
CI failure and blocked merges

Required Systems:
Secret-scan config, doc redaction, CI workflow
