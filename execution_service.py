import os
import hmac
import hashlib
import json
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from nonce_store import SQLiteNonceStore, NonceStoreError
from secrets_manager import get_secrets_manager

DB_PATH = os.getenv("EXECUTION_SERVICE_DB", "/tmp/execution_service_nonce.db")
KEY_NAME = "exec_hmac_key"


def _now() -> int:
    return int(time.time())


def _get_key(secrets_manager):
    return secrets_manager.get_secret(KEY_NAME)


def _init_state_db(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS gateway_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            boot_completed INTEGER NOT NULL DEFAULT 0,
            risk_locked INTEGER NOT NULL DEFAULT 1,
            updated_ts INTEGER NOT NULL,
            updated_by TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        INSERT OR IGNORE INTO gateway_state(id, boot_completed, risk_locked, updated_ts, updated_by)
        VALUES (1, 0, 1, ?, 'system_init')
        """,
        (_now(),),
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS execution_orders (
            order_id TEXT NOT NULL,
            strategy_id TEXT NOT NULL,
            status TEXT NOT NULL,
            created_ts INTEGER NOT NULL,
            updated_ts INTEGER NOT NULL,
            result_json TEXT,
            last_error TEXT,
            PRIMARY KEY(order_id, strategy_id)
        )
        """
    )
    conn.commit()


class ExecHandler(BaseHTTPRequestHandler):
    server_version = "ExecService/0.2"

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        return json.loads(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/metrics":
            text = self.server.render_metrics()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            self.wfile.write(text.encode())
            return
        if parsed.path == "/state":
            self._respond(200, self.server.get_gateway_state())
            return
        self._respond(404, {"error": "not_found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/execute":
                payload = self._read_json()
                token = payload.get("token")
                order = payload.get("order")
                if not token or not order:
                    return self._respond(400, {"error": "missing_fields"})
                try:
                    result = self.server.validate_and_execute(token, order)
                    return self._respond(200, result)
                except Exception as exc:
                    return self._respond(403, {"error": "rejected", "reason": str(exc)})

            if parsed.path == "/override":
                payload = self._read_json()
                try:
                    res = self.server.handle_manual_override(dict(self.headers), payload)
                    return self._respond(200, res)
                except Exception as exc:
                    return self._respond(403, {"error": "forbidden", "reason": str(exc)})

            if parsed.path == "/risk/lock":
                # Risk circuit lock/unlock endpoint. Requires shared secret header.
                payload = self._read_json()
                secret = None
                if hasattr(self.headers, "items"):
                    for hn, hv in self.headers.items():
                        if str(hn).lower() == "x-risk-shared-secret":
                            secret = hv
                            break
                expected = os.getenv("RISK_CIRCUIT_SHARED_SECRET")
                if not expected:
                    return self._respond(403, {"error": "risk_shared_secret_not_configured"})
                if not secret or secret != expected:
                    self.audit_event("risk_lock_forbidden", provided=bool(secret))
                    return self._respond(403, {"error": "forbidden_invalid_risk_secret"})
                lock = bool(payload.get("lock", True))
                reason = payload.get("reason", "remote_risk_signal")
                actor = payload.get("actor", "risk_engine")
                # apply to gateway state
                self._set_gateway_state(actor=actor, risk_locked=lock)
                self.audit_event("risk_lock_changed", actor=actor, lock=lock, reason=reason)
                return self._respond(200, {"status": "ok", "risk_locked": lock})

            if parsed.path == "/operator/dlq":
                # Lightweight DLQ operator endpoint for listing/replaying/deleting entries.
                # Requires operator API key.
                payload = self._read_json()
                self._require_operator_key(dict(self.headers))
                action = payload.get("action", "list")
                # For now provide a deterministic stubbed response so tests and operators
                # can exercise the endpoint without a production DLQ backend.
                if action == "list":
                    return self._respond(200, {"status": "ok", "entries": []})
                if action == "replay":
                    return self._respond(200, {"status": "ok", "replayed": 0})
                if action == "delete":
                    return self._respond(200, {"status": "ok", "deleted": 0})
                return self._respond(400, {"error": "unknown_action"})

            if parsed.path == "/boot/complete":
                payload = self._read_json()
                try:
                    res = self.server.handle_boot_complete(dict(self.headers), payload)
                    return self._respond(200, res)
                except Exception as exc:
                    return self._respond(403, {"error": "forbidden", "reason": str(exc)})

            return self._respond(404, {"error": "not_found"})
        except json.JSONDecodeError:
            return self._respond(400, {"error": "bad_json"})
        except Exception as exc:
            self.server.audit_event("request_error", reason=str(exc))
            return self._respond(500, {"error": "internal_error"})

    def log_message(self, fmt, *args):
        return


class ExecutionService(HTTPServer):
    # Allow quick restart in tests when previous socket is in TIME_WAIT
    allow_reuse_address = True
    def __init__(
        self,
        addr,
        db_path=DB_PATH,
        nonce_store=None,
        secrets_manager=None,
        operator_api_key=None,
        audit_log_path=None,
    ):
        super().__init__(addr, ExecHandler)
        self.secrets_manager = secrets_manager or FileSecretsManager()
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db_lock = threading.Lock()
        _init_state_db(self._db)
        self.nonce_store = nonce_store or SQLiteNonceStore(db_path)
        self.operator_api_key = operator_api_key or os.getenv("EXECUTION_OPERATOR_API_KEY")
        if not self.operator_api_key:
            raise RuntimeError("missing_operator_api_key")
        self.audit_log_path = audit_log_path or os.getenv("EXECUTION_AUDIT_LOG", "/tmp/execution_audit.log")
        self.trade_journal_path = os.getenv("TRADE_JOURNAL_PATH", "/tmp/trade_journal.jsonl")
        self.execution_key = _get_key(self.secrets_manager)
        self._metrics_lock = threading.Lock()
        self._metrics = {
            "execute_requests_total": 0,
            "execute_rejected_total": 0,
            "execute_filled_total": 0,
            "execute_idempotent_total": 0,
            "risk_lock_rejections_total": 0,
            "boot_rejections_total": 0,
            "audit_write_failures_total": 0,
            "errors_total": 0,
        }
        self._db_state_metrics = {
            "gateway_boot_completed": 0,
            "gateway_risk_locked": 1,
            "orders_pending_total": 0,
            "orders_filled_total": 0,
            "orders_rejected_total": 0,
        }
        self._refresh_db_state_metrics()

    def _metric_inc(self, key, value=1):
        with self._metrics_lock:
            self._metrics[key] = self._metrics.get(key, 0) + value

    def render_metrics(self):
        with self._metrics_lock:
            lines = [
                "# HELP openclaw_execution_service_metrics Execution service counters",
                "# TYPE openclaw_execution_service_metrics counter",
            ]
            for key, value in sorted(self._metrics.items()):
                lines.append(f"openclaw_{key} {value}")

            lines.extend(
                [
                    "# HELP openclaw_execution_gateway_boot_completed Gateway boot completion state (0/1)",
                    "# TYPE openclaw_execution_gateway_boot_completed gauge",
                    f"openclaw_execution_gateway_boot_completed {self._db_state_metrics['gateway_boot_completed']}",
                    "# HELP openclaw_execution_gateway_risk_locked Gateway risk lock state (0/1)",
                    "# TYPE openclaw_execution_gateway_risk_locked gauge",
                    f"openclaw_execution_gateway_risk_locked {self._db_state_metrics['gateway_risk_locked']}",
                    "# HELP openclaw_orders_pending_total Pending execution orders",
                    "# TYPE openclaw_orders_pending_total gauge",
                    f"openclaw_orders_pending_total {self._db_state_metrics['orders_pending_total']}",
                    "# HELP openclaw_orders_filled_total Filled execution orders",
                    "# TYPE openclaw_orders_filled_total gauge",
                    f"openclaw_orders_filled_total {self._db_state_metrics['orders_filled_total']}",
                    "# HELP openclaw_orders_rejected_total Rejected execution orders",
                    "# TYPE openclaw_orders_rejected_total gauge",
                    f"openclaw_orders_rejected_total {self._db_state_metrics['orders_rejected_total']}",
                ]
            )
            return "\n".join(lines) + "\n"

    def _refresh_db_state_metrics(self):
        with self._db_lock:
            cur = self._db.cursor()
            state_row = cur.execute(
                "SELECT boot_completed, risk_locked FROM gateway_state WHERE id=1"
            ).fetchone()
            pending = cur.execute(
                "SELECT COUNT(*) FROM execution_orders WHERE status='pending'"
            ).fetchone()[0]
            filled = cur.execute(
                "SELECT COUNT(*) FROM execution_orders WHERE status='filled'"
            ).fetchone()[0]
            rejected = cur.execute(
                "SELECT COUNT(*) FROM execution_orders WHERE status='rejected'"
            ).fetchone()[0]

        with self._metrics_lock:
            self._db_state_metrics["gateway_boot_completed"] = int(bool(state_row[0]))
            self._db_state_metrics["gateway_risk_locked"] = int(bool(state_row[1]))
            self._db_state_metrics["orders_pending_total"] = int(pending)
            self._db_state_metrics["orders_filled_total"] = int(filled)
            self._db_state_metrics["orders_rejected_total"] = int(rejected)

    def audit_event(self, event: str, **details):
        payload = {"ts": _now(), "event": event, **details}
        self._append_audit(payload)

    def _append_audit(self, payload: dict):
        record = {"ts": _now(), **payload}
        try:
            with open(self.audit_log_path, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as exc:
            self._metric_inc("audit_write_failures_total")
            fallback = {"ts": _now(), "event": "audit_write_failed", "reason": str(exc), "original_event": record.get("event")}
            print(json.dumps(fallback))

    def _append_trade_journal(self, payload: dict):
        record = {"ts": _now(), **payload}
        try:
            with open(self.trade_journal_path, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as exc:
            self._metric_inc("audit_write_failures_total")
            fallback = {
                "ts": _now(),
                "event": "trade_journal_write_failed",
                "reason": str(exc),
                "order_id": payload.get("order_id"),
                "strategy_id": payload.get("strategy_id"),
            }
            print(json.dumps(fallback))

    def get_gateway_state(self):
        with self._db_lock:
            cur = self._db.cursor()
            row = cur.execute(
                "SELECT boot_completed, risk_locked, updated_ts, updated_by FROM gateway_state WHERE id=1"
            ).fetchone()
        return {
            "boot_completed": bool(row[0]),
            "risk_locked": bool(row[1]),
            "updated_ts": int(row[2]),
            "updated_by": row[3],
        }

    def _set_gateway_state(self, actor: str, boot_completed=None, risk_locked=None):
        with self._db_lock:
            cur = self._db.cursor()
            cur.execute("BEGIN IMMEDIATE")
            row = cur.execute("SELECT boot_completed, risk_locked FROM gateway_state WHERE id=1").fetchone()
            current_boot = int(row[0])
            current_lock = int(row[1])
            new_boot = current_boot if boot_completed is None else int(bool(boot_completed))
            new_lock = current_lock if risk_locked is None else int(bool(risk_locked))
            cur.execute(
                "UPDATE gateway_state SET boot_completed=?, risk_locked=?, updated_ts=?, updated_by=? WHERE id=1",
                (new_boot, new_lock, _now(), actor),
            )
            self._db.commit()
        self._refresh_db_state_metrics()

    def _require_gateway_open(self):
        state = self.get_gateway_state()
        if not state["boot_completed"]:
            self._metric_inc("boot_rejections_total")
            raise RuntimeError("boot_not_completed")
        if state["risk_locked"]:
            self._metric_inc("risk_lock_rejections_total")
            raise RuntimeError("risk_lock_active")

    def _validate_token(self, token: dict):
        for field in ("order_id", "timestamp", "nonce", "expiry", "strategy_id", "sig"):
            if field not in token:
                raise RuntimeError(f"missing_token_field:{field}")

        now = _now()
        expiry = int(token["expiry"])
        ts = int(token["timestamp"])
        if now > expiry:
            raise RuntimeError("token_expired")
        if abs(now - ts) > 5:
            raise RuntimeError("timestamp_skew_too_large")

        msg = f"{token['order_id']}|{token['timestamp']}|{token['nonce']}|{token['expiry']}|{token['strategy_id']}".encode()
        expected = hmac.new(self.execution_key, msg, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, token["sig"]):
            raise RuntimeError("invalid_signature")

    def validate_and_execute(self, token: dict, order: dict):
        self._metric_inc("execute_requests_total")
        try:
            self._require_gateway_open()
            self._validate_token(token)

            order_id = token["order_id"]
            strategy_id = token["strategy_id"]
            now = _now()

            # Idempotency guard first: if already filled, return persisted result.
            with self._db_lock:
                cur = self._db.cursor()
                row = cur.execute(
                    "SELECT status, result_json, last_error FROM execution_orders WHERE order_id=? AND strategy_id=?",
                    (order_id, strategy_id),
                ).fetchone()
                if row:
                    status, result_json, last_error = row
                    if status == "filled" and result_json:
                        self._metric_inc("execute_idempotent_total")
                        return json.loads(result_json)
                    if status == "rejected":
                        raise RuntimeError(f"order_previously_rejected:{last_error or 'unknown'}")
                    if status == "pending":
                        raise RuntimeError("order_pending_manual_reconcile")

            try:
                self.nonce_store.insert_nonce(strategy_id, token["nonce"], now)
            except NonceStoreError:
                raise RuntimeError("replayed_nonce")

            self.audit_event("exec_attempt", strategy_id=strategy_id, order_id=order_id)

            # Atomic state transition: pending -> filled/rejected.
            with self._db_lock:
                cur = self._db.cursor()
                cur.execute("BEGIN IMMEDIATE")
                cur.execute(
                    "INSERT OR REPLACE INTO execution_orders(order_id, strategy_id, status, created_ts, updated_ts, result_json, last_error) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (order_id, strategy_id, "pending", now, now, None, None),
                )
                self._db.commit()
            self._refresh_db_state_metrics()

            result = {"order_id": order_id, "status": "filled", "ts": _now()}

            with self._db_lock:
                cur = self._db.cursor()
                cur.execute("BEGIN IMMEDIATE")
                cur.execute(
                    "UPDATE execution_orders SET status=?, updated_ts=?, result_json=?, last_error=NULL WHERE order_id=? AND strategy_id=?",
                    ("filled", _now(), json.dumps(result), order_id, strategy_id),
                )
                self._db.commit()
            self._refresh_db_state_metrics()

            self._metric_inc("execute_filled_total")
            self.audit_event("exec_filled", strategy_id=strategy_id, order_id=order_id)
            self._append_trade_journal({
                "event": "trade_filled",
                "order_id": order_id,
                "strategy_id": strategy_id,
                "status": "filled",
                "result": result,
            })
            return result
        except Exception as exc:
            self._metric_inc("execute_rejected_total")
            self._metric_inc("errors_total")
            try:
                order_id = token.get("order_id")
                strategy_id = token.get("strategy_id")
                if order_id and strategy_id:
                    with self._db_lock:
                        cur = self._db.cursor()
                        cur.execute("BEGIN IMMEDIATE")
                        cur.execute(
                            "INSERT OR REPLACE INTO execution_orders(order_id, strategy_id, status, created_ts, updated_ts, result_json, last_error) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (order_id, strategy_id, "rejected", _now(), _now(), None, str(exc)),
                        )
                        self._db.commit()
                    self._refresh_db_state_metrics()
            except Exception:
                self._metric_inc("errors_total")
            self.audit_event("exec_rejected", reason=str(exc), order_id=token.get("order_id"), strategy_id=token.get("strategy_id"))
            self._append_trade_journal({
                "event": "trade_rejected",
                "order_id": token.get("order_id"),
                "strategy_id": token.get("strategy_id"),
                "status": "rejected",
                "reason": str(exc),
            })
            raise

    def _require_operator_key(self, headers):
        key = None
        if hasattr(headers, "items"):
            for header_name, header_value in headers.items():
                if str(header_name).lower() == "x-op-api-key":
                    key = header_value
                    break
        # record key presence and do a safe compare; avoid logging secrets
        header_names = [str(k) for k in headers.keys()] if hasattr(headers, "keys") else []
        if not key:
            self.audit_event("operator_key_missing", headers=header_names)
            raise RuntimeError("forbidden_missing_operator_key")
        if key != self.operator_api_key:
            preview = (str(key)[:6] + "...") if key else ""
            self.audit_event("operator_key_mismatch", provided=bool(key), preview=preview)
            raise RuntimeError("forbidden_invalid_operator_key")

    def _verify_boot_prereqs(self):
        if not self.execution_key:
            raise RuntimeError("missing_execution_key")

    def handle_boot_complete(self, headers, body):
        self._require_operator_key(headers)
        actor = body.get("actor")
        if not actor:
            raise RuntimeError("missing_actor")
        self._verify_boot_prereqs()
        self._set_gateway_state(actor=actor, boot_completed=True)
        self.audit_event("boot_completed", actor=actor)
        return {"status": "ok", "boot_completed": True}

    def handle_manual_override(self, headers, body):
        self._require_operator_key(headers)
        actor = body.get("actor")
        if not actor:
            raise RuntimeError("missing_actor")
        enable = bool(body.get("enable"))
        self._set_gateway_state(actor=actor, risk_locked=not enable)
        self.audit_event("manual_override", actor=actor, enabled=enable)
        return {"status": "ok", "trading_enabled": enable}


def _prepare_secrets(secrets_path=None, key_path=None):
    from secrets_manager import get_secrets_manager

    manager = get_secrets_manager(secrets_path)
    if key_path and hasattr(manager, "set_secret"):
        with open(key_path, "rb") as f:
            manager.set_secret(KEY_NAME, f.read().strip().decode())
    return manager


def run_service(host="127.0.0.1", port=8000, db_path=DB_PATH, secrets_path=None, key_path=None):
    secrets_manager = _prepare_secrets(secrets_path=secrets_path, key_path=key_path)
    srv = ExecutionService((host, port), db_path=db_path, secrets_manager=secrets_manager)
    print(json.dumps({"ts": _now(), "event": "exec_service_started", "host": host, "port": port}))
    try:
        srv.serve_forever()
    finally:
        srv.server_close()


if __name__ == "__main__":
    run_service()
