import os
import pytest
import time
import os
import sys

# ensure package imports work from this path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import subprocess
import tempfile
import socket
import threading
import json
import urllib.request
import urllib.error
from execution_service import run_service
from risk_engine import RiskEngine, RiskException
from models import Order


def _start_exec_service(secrets_path, port=8002):
    # start in a background thread
    def _run():
        run_service(host="127.0.0.1", port=port, secrets_path=secrets_path)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    for _ in range(30):
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=0.2)
            s.close()
            break
        except Exception:
            time.sleep(0.05)

    boot_payload = json.dumps({"actor": "pytest"}).encode()
    boot_req = urllib.request.Request(f"http://127.0.0.1:{port}/boot/complete", data=boot_payload, headers={"Content-Type": "application/json", "X-OP-API-KEY": "test-operator-key"})
    with urllib.request.urlopen(boot_req, timeout=2):
        pass
    override_payload = json.dumps({"actor": "pytest", "enable": True}).encode()
    override_req = urllib.request.Request(f"http://127.0.0.1:{port}/override", data=override_payload, headers={"Content-Type": "application/json", "X-OP-API-KEY": "test-operator-key"})
    with urllib.request.urlopen(override_req, timeout=2):
        pass
    return t


@pytest.fixture(scope="module", autouse=True)
def set_secret_env():
    import tempfile
    key = b"test-secret-123"
    secrets_fd, secrets_path = tempfile.mkstemp()
    os.close(secrets_fd)
    # Initialize secrets file as valid JSON
    with open(secrets_path, "w") as f:
        f.write("{}")
    from secrets_manager import FileSecretsManager
    sm = FileSecretsManager(secrets_path)
    sm.set_secret("signer_hmac_key", key.decode())
    sm.set_secret("exec_hmac_key", key.decode())
    os.environ["SECRETS_FILE_PATH"] = secrets_path
    os.environ["STRATEGY_ID"] = "test-strat"
    os.environ["SIGNER_API_KEY"] = "test-signer-api"
    os.environ["EXECUTION_OPERATOR_API_KEY"] = "test-operator-key"
    os.environ["SIGNER_URL"] = "http://127.0.0.1:9002/sign"
    os.environ["EXEC_SERVICE_URL"] = "http://127.0.0.1:8002/execute"
    signer_thread = threading.Thread(target=lambda: __import__("signer_service").run_service(host="127.0.0.1", port=9002, secrets_path=secrets_path, api_key="test-signer-api"), daemon=True)
    signer_thread.start()
    import socket
    for _ in range(20):
        try:
            s = socket.create_connection(("127.0.0.1", 9002), timeout=0.1)
            s.close()
            break
        except Exception:
            time.sleep(0.05)
    yield
    # keep secrets file available for signer thread lifetime


def test_execute_happy_path():
    import tempfile
    secrets_fd, secrets_path = tempfile.mkstemp()
    os.close(secrets_fd)
    from secrets_manager import FileSecretsManager
    key = "test-secret-123"
    sm = FileSecretsManager(secrets_path)
    sm.set_secret("signer_hmac_key", key)
    sm.set_secret("exec_hmac_key", key)
    t = _start_exec_service(secrets_path)
    re = RiskEngine(None)
    order = Order(symbol="BTCUSD", quantity=1, price=10000)
    res = re.submit_order(order, signal="test")
    assert res["status"] == "filled"
    try:
        os.unlink(secrets_path)
    except Exception:
        pass


def test_daily_loss_cap_triggers():
    re = RiskEngine(None, daily_loss_cap=100)
    # Force pnl beyond cap
    re._pnl = -200
    order = Order(symbol="BTCUSD", quantity=1, price=10000)
    with pytest.raises(RiskException):
        re.submit_order(order)


def test_exposure_limit():
    re = RiskEngine(None, per_asset_limit=5_000)
    order = Order(symbol="BTCUSD", quantity=1, price=2000)
    # this is ok
    re.submit_order(order)
    large = Order(symbol="BTCUSD", quantity=2, price=2000)
    # now positions would exceed
    with pytest.raises(RiskException):
        re.submit_order(large)


def test_leverage_rejection():
    re = RiskEngine(None, leverage_limit=0.005)
    order = Order(symbol="ETHUSD", quantity=10, price=100)
    with pytest.raises(RiskException):
        re.submit_order(order)


def test_circuit_breaker():
    re = RiskEngine(None, circuit_atr_threshold=1000)
    order = Order(symbol="X", quantity=2, price=600)
    with pytest.raises(RiskException):
        re.submit_order(order)


def test_trade_frequency_guard():
    re = RiskEngine(None, trade_frequency_limit=2, trade_window_seconds=1)
    order = Order(symbol="A", quantity=1, price=1)
    re.submit_order(order)
    re.submit_order(order)
    with pytest.raises(RiskException):
        re.submit_order(order)


def test_bounded_retry_transient_failure_then_success(monkeypatch):
    re = RiskEngine(None)

    class _TokenFactory:
        def new_token(self, order_id):
            return {
                "order_id": order_id,
                "timestamp": int(time.time()),
                "nonce": "n1",
                "expiry": int(time.time()) + 5,
                "strategy_id": "test-strat",
                "sig": "sig",
            }

    re._token_factory = _TokenFactory()

    call_count = {"n": 0}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({"order_id": "order-retry", "status": "filled", "ts": int(time.time())}).encode()

    def _fake_urlopen(req, timeout=5):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise urllib.error.URLError("transient network error")
        return _Resp()

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    monkeypatch.setenv("EXEC_RPC_MAX_ATTEMPTS", "2")
    monkeypatch.setenv("EXEC_RPC_RETRY_BACKOFF_SECONDS", "0")

    # ensure these values apply for this instance
    re.exec_rpc_max_attempts = 2
    re.exec_rpc_retry_backoff_seconds = 0.0

    order = Order(symbol="BTCUSD", quantity=1, price=100)
    result = re.submit_order(order)

    assert result["status"] == "filled"
    assert call_count["n"] == 2
    assert re._positions["BTCUSD"] == 100
    assert re._notional == 100


def test_wallet_balance_env_is_enforced(monkeypatch):
    monkeypatch.setenv("WALLET_BALANCE", "250")
    re = RiskEngine(None)

    class _TokenFactory:
        def new_token(self, order_id):
            return {"order_id": order_id}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({"order_id": "order-wallet", "status": "filled", "ts": int(time.time())}).encode()

    def _fake_urlopen(req, timeout=5):
        return _Resp()

    re._token_factory = _TokenFactory()
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    with pytest.raises(RiskException, match="Insufficient wallet balance for order notional"):
        re.submit_order(Order(symbol="BTCUSD", quantity=1, price=300))


def test_near_zero_wallet_balance_fails_closed(monkeypatch):
    monkeypatch.setenv("WALLET_BALANCE", "0.0000001")
    monkeypatch.setenv("MIN_WALLET_BALANCE", "0.000001")
    re = RiskEngine(None)

    with pytest.raises(RiskException, match="Insufficient wallet balance"):
        re.submit_order(Order(symbol="BTCUSD", quantity=0.001, price=1))


def test_invalid_wallet_balance_source_fails_closed(monkeypatch):
    monkeypatch.setenv("WALLET_BALANCE", "nan")
    with pytest.raises(RiskException, match="Invalid wallet balance source"):
        RiskEngine(None)


def test_submit_order_is_race_safe(monkeypatch):
    monkeypatch.setenv("WALLET_BALANCE", "1000")
    re = RiskEngine(None, gross_exposure_limit=150, per_asset_limit=1_000_000, net_exposure_limit=1_000_000)

    class _TokenFactory:
        def new_token(self, order_id):
            return {"order_id": order_id}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({"order_id": "order-race", "status": "filled", "ts": int(time.time())}).encode()

    def _fake_urlopen(req, timeout=5):
        time.sleep(0.1)
        return _Resp()

    re._token_factory = _TokenFactory()
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    outcomes = []

    def _submit(order_id):
        try:
            re.submit_order(Order(symbol="BTCUSD", quantity=1, price=100, order_id=order_id))
            outcomes.append("ok")
        except Exception:
            outcomes.append("rejected")

    t1 = threading.Thread(target=_submit, args=("race-1",))
    t2 = threading.Thread(target=_submit, args=("race-2",))
    t1.start()
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)

    assert outcomes.count("ok") == 1
    assert outcomes.count("rejected") == 1


def test_startup_wallet_preflight_logs_config(caplog, monkeypatch):
    monkeypatch.setenv("WALLET_BALANCE", "50")
    monkeypatch.setenv("MIN_WALLET_BALANCE", "0.000001")

    with caplog.at_level("INFO", logger="risk_engine"):
        RiskEngine(None)

    assert any('"event": "wallet_preflight_config_valid"' in rec.message for rec in caplog.records)
