import os
import time
import json
import tempfile
import threading
import urllib.request
import urllib.error
import pytest

import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from execution_service import run_service
from risk_engine import ExecutionTokenFactory
from models import Order


@pytest.fixture(scope="module")
def exec_service():
    # prepare key file
    key = b"test-secret-123"
    fd, keypath = tempfile.mkstemp()
    os.write(fd, key)
    os.close(fd)
    secrets_fd, secrets_path = tempfile.mkstemp()
    os.close(secrets_fd)
    # initialize secrets file and preload exec key so ExecutionService boot prereqs pass
    with open(secrets_path, "w") as f:
        json.dump({"exec_hmac_key": key.decode()}, f)
    # Do NOT set RISK_EXECUTOR_SHARED_SECRET here; signer issues tokens.
    os.environ.pop("RISK_EXECUTOR_SHARED_SECRET", None)
    os.environ["STRATEGY_ID"] = "integration-strat"
    os.environ["EXECUTION_OPERATOR_API_KEY"] = "test-operator-key"

    # start signer with same key and an api key
    api_key = "test-signer-api"
    os.environ["SIGNER_API_KEY"] = api_key
    signer_thread = threading.Thread(target=lambda: __import__("signer_service").run_service(host="127.0.0.1", port=9000, key_path=keypath, secrets_path=secrets_path, api_key=api_key), daemon=True)
    signer_thread.start()
    # wait for signer to accept connections
    import socket
    for _ in range(20):
        try:
            s = socket.create_connection(("127.0.0.1", 9000), timeout=0.1)
            s.close()
            break
        except Exception:
            time.sleep(0.05)

    # pick an available port so tests can run reliably in parallel/environments
    import socket as _socket
    s = _socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()

    # export port for helper functions below
    os.environ["EXEC_SERVICE_PORT"] = str(port)

    def _run():
        run_service(host="127.0.0.1", port=port, key_path=keypath, secrets_path=secrets_path)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    # wait for server to accept connections (give it a bit longer)
    import socket
    for _ in range(60):
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=0.2)
            s.close()
            break
        except Exception:
            time.sleep(0.05)

    # complete boot then unlock trading (fail-safe default is locked)
    boot_url = f"http://127.0.0.1:{port}/boot/complete"
    boot_payload = json.dumps({"actor": "pytest"}).encode()
    boot_req = urllib.request.Request(boot_url, data=boot_payload, headers={"Content-Type": "application/json", "X-OP-API-KEY": "test-operator-key"})
    with urllib.request.urlopen(boot_req, timeout=5):
        pass
    override_url = f"http://127.0.0.1:{port}/override"
    override_payload = json.dumps({"actor": "pytest", "enable": True}).encode()
    override_req = urllib.request.Request(override_url, data=override_payload, headers={"Content-Type": "application/json", "X-OP-API-KEY": "test-operator-key"})
    with urllib.request.urlopen(override_req, timeout=5):
        pass

    yield
    try:
        os.unlink(keypath)
    except Exception:
        pass
    try:
        os.unlink(secrets_path)
    except Exception:
        pass


def _post_execute(token, order):
    port = os.getenv("EXEC_SERVICE_PORT", "8000")
    url = f"http://127.0.0.1:{port}/execute"
    payload = json.dumps({"token": token, "order": order}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.getcode(), json.loads(resp.read())
    except urllib.error.HTTPError as he:
        body = he.read()
        try:
            return he.code, json.loads(body)
        except Exception:
            return he.code, {"error": "http_error"}


def test_invalid_signature(exec_service):
    etf = ExecutionTokenFactory()
    token = etf.new_token("order-1")
    # tamper signature
    token["sig"] = "deadbeef"
    order = {"symbol": "BTCUSD", "quantity": 1, "price": 10000, "order_id": "order-1"}
    code, body = _post_execute(token, order)
    assert code == 403
    assert body.get("error") == "rejected"
    assert "invalid_signature" in body.get("reason", "")


def test_expired_token(exec_service):
    etf = ExecutionTokenFactory()
    token = etf.new_token("order-2")
    # set expiry in past
    token["expiry"] = int(time.time()) - 10
    order = {"symbol": "BTCUSD", "quantity": 1, "price": 10000, "order_id": "order-2"}
    code, body = _post_execute(token, order)
    assert code == 403
    assert body.get("error") == "rejected"
    assert "token_expired" in body.get("reason", "")


def test_replayed_nonce(exec_service):
    etf = ExecutionTokenFactory()
    token = etf.new_token("order-3")
    order = {"symbol": "BTCUSD", "quantity": 1, "price": 10000, "order_id": "order-3"}
    code, body = _post_execute(token, order)
    assert code == 200
    # replay same token should be idempotent (no second execution side effect)
    code2, body2 = _post_execute(token, order)
    assert code2 == 200
    assert body2.get("order_id") == token["order_id"]
    assert body2.get("status") == "filled"


def test_gateway_risk_lock_blocks_execution(exec_service):
    # lock gateway and verify execution is blocked even with valid signed token
    override_url = f"http://127.0.0.1:{os.getenv('EXEC_SERVICE_PORT','8000')}/override"
    lock_payload = json.dumps({"actor": "operator1", "enable": False}).encode()
    lock_req = urllib.request.Request(override_url, data=lock_payload, headers={"Content-Type": "application/json", "X-OP-API-KEY": "test-operator-key"})
    with urllib.request.urlopen(lock_req, timeout=2):
        pass

    etf = ExecutionTokenFactory()
    token = etf.new_token("order-lock")
    order = {"symbol": "BTCUSD", "quantity": 1, "price": 10000, "order_id": "order-lock"}
    code, body = _post_execute(token, order)
    assert code == 403
    assert "risk_lock_active" in body.get("reason", "")

    unlock_payload = json.dumps({"actor": "operator1", "enable": True}).encode()
    unlock_req = urllib.request.Request(override_url, data=unlock_payload, headers={"Content-Type": "application/json", "X-OP-API-KEY": "test-operator-key"})
    with urllib.request.urlopen(unlock_req, timeout=2):
        pass


def test_operator_manual_override(exec_service):
    # Test manual override endpoint with correct and incorrect API key
    url = f"http://127.0.0.1:{os.getenv('EXEC_SERVICE_PORT','8000')}/override"
    payload = json.dumps({"actor": "operator1", "enable": True}).encode()
    # Correct key
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "X-OP-API-KEY": os.environ.get("EXECUTION_OPERATOR_API_KEY", "test-operator-key")})
    with urllib.request.urlopen(req, timeout=2) as resp:
        assert resp.getcode() == 200
        body = json.loads(resp.read())
        assert body["status"] == "ok"
    # Incorrect key
    req_bad = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "X-OP-API-KEY": "wrong-key"})
    try:
        urllib.request.urlopen(req_bad, timeout=2)
        assert False, "Should not allow override with wrong key"
    except urllib.error.HTTPError as he:
        assert he.code == 403
        body = json.loads(he.read())
        assert body["error"] == "forbidden"

def test_secrets_manager_key_retrieval():
    from secrets_manager import FileSecretsManager
    key_name = "exec_hmac_key"
    test_val = "supersecretkey"
    sm = FileSecretsManager()
    sm.set_secret(key_name, test_val)
    val = sm.get_secret(key_name)
    assert val == test_val.encode()


def test_metrics_endpoint(exec_service):
    req = urllib.request.Request(f"http://127.0.0.1:{os.getenv('EXEC_SERVICE_PORT','8000')}/metrics")
    with urllib.request.urlopen(req, timeout=2) as resp:
        assert resp.getcode() == 200
        body = resp.read().decode()
        assert "openclaw_execute_requests_total" in body
        assert "openclaw_execute_rejected_total" in body
        assert "openclaw_execute_idempotent_total" in body
        assert "openclaw_execution_gateway_boot_completed" in body
        assert "openclaw_execution_gateway_risk_locked" in body
        assert "openclaw_orders_filled_total" in body
        # ensure no sensitive values are exported
        assert "exec_hmac_key" not in body
        assert "signer_hmac_key" not in body


def test_metrics_match_db_state(exec_service):
    import sqlite3
    req = urllib.request.Request(f"http://127.0.0.1:{os.getenv('EXEC_SERVICE_PORT','8000')}/metrics")
    with urllib.request.urlopen(req, timeout=2) as resp:
        body = resp.read().decode().splitlines()

    metrics = {}
    for line in body:
        if not line or line.startswith("#"):
            continue
        name, value = line.split(" ", 1)
        metrics[name.strip()] = float(value.strip())

    db = os.getenv("EXECUTION_SERVICE_DB", "/tmp/execution_service_nonce.db")
    conn = sqlite3.connect(db)
    try:
        state = conn.execute("SELECT boot_completed, risk_locked FROM gateway_state WHERE id=1").fetchone()
        pending = conn.execute("SELECT COUNT(*) FROM execution_orders WHERE status='pending'").fetchone()[0]
        filled = conn.execute("SELECT COUNT(*) FROM execution_orders WHERE status='filled'").fetchone()[0]
        rejected = conn.execute("SELECT COUNT(*) FROM execution_orders WHERE status='rejected'").fetchone()[0]
    finally:
        conn.close()

    assert metrics["openclaw_execution_gateway_boot_completed"] == float(int(state[0]))
    assert metrics["openclaw_execution_gateway_risk_locked"] == float(int(state[1]))
    assert metrics["openclaw_orders_pending_total"] == float(pending)
    assert metrics["openclaw_orders_filled_total"] == float(filled)
    assert metrics["openclaw_orders_rejected_total"] == float(rejected)


def test_nonce_schema_constraints(exec_service):
    import sqlite3
    db = os.getenv("EXECUTION_SERVICE_DB", "/tmp/execution_service_nonce.db")
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute("PRAGMA table_info('nonces')").fetchall()
        by_name = {row[1]: row for row in rows}
        assert by_name["strategy_id"][3] == 1
        assert by_name["nonce"][3] == 1
        assert by_name["ts"][3] == 1
    finally:
        conn.close()


def test_execution_order_state_persisted(exec_service):
    import sqlite3
    db = os.getenv("EXECUTION_SERVICE_DB", "/tmp/execution_service_nonce.db")
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute("PRAGMA table_info('execution_orders')").fetchall()
        by_name = {row[1]: row for row in rows}
        assert by_name["order_id"][3] == 1
        assert by_name["strategy_id"][3] == 1
        assert by_name["status"][3] == 1
        assert by_name["created_ts"][3] == 1
        assert by_name["updated_ts"][3] == 1
    finally:
        conn.close()

def test_rpc_failure_blocks_order(monkeypatch):
    # ensure service not running on 9000
    monkeypatch.setenv("EXEC_SERVICE_URL", "http://127.0.0.1:9000/execute")
    os.environ.setdefault("RISK_EXECUTOR_SHARED_SECRET", "test-secret-123")
    os.environ.setdefault("STRATEGY_ID", "integration-strat")
    from risk_engine import RiskEngine
    re = RiskEngine(None)
    order = Order(symbol="BTCUSD", quantity=1, price=10000)
    import pytest
    with pytest.raises(Exception):
        re.submit_order(order)
