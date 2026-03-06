import time
import json
import urllib.request
import urllib.error
from unittest import mock

import pytest

from risk_engine import RiskEngine, RiskException
from exchange_backoff import call_with_backoff


def test_heartbeat_timeout_latches_safe_mode(tmp_path):
    re = RiskEngine(wallet_balance_provider=lambda: 100000.0)
    # heartbeat monitor test does not require changing RPC retry config
    # start monitor with short timeout
    re.start_heartbeat_monitor(interval_seconds=0.1, timeout_seconds=0.5)
    # do not ping; wait for monitor to trigger
    time.sleep(1.0)
    assert re._kill_switch is True
    re.stop_heartbeat_monitor()


def test_data_drift_blocks_execution():
    re = RiskEngine(wallet_balance_provider=lambda: 100000.0)
    

    # provider returns a timestamp 10 seconds in the past
    def stale_provider(symbol):
        return time.time() - 10.0

    re.set_market_data_provider(stale_provider, max_age_seconds=5)

    class DummyOrder:
        def __init__(self):
            self.order_id = "o1"
            self.symbol = "BTCUSD"
            self.quantity = 1
            self.price = 100
        def as_dict(self):
            return {"order_id": self.order_id, "symbol": self.symbol, "quantity": self.quantity, "price": self.price}

    with pytest.raises(RiskException):
        re.submit_order(DummyOrder())


def test_api_failure_triggers_retry(monkeypatch):
    # simulate an execution service that returns HTTPError 502 twice then a valid response
    calls = {"n": 0}

    class FakeResp:
        def __init__(self, data):
            self._data = data
        def read(self):
            return self._data
        def getcode(self):
            return 200
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(req, timeout=5):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise urllib.error.HTTPError(url=req.full_url, code=502, msg="Bad Gateway", hdrs=None, fp=None)
        return FakeResp(json.dumps({"order_id": "o1", "status": "filled", "pnl_change": 0.0}).encode())

    monkeypatch.setattr('urllib.request.urlopen', fake_urlopen)

    re = RiskEngine(wallet_balance_provider=lambda: 100000.0)
    re.exec_rpc_max_attempts = 4

    class DummyOrder:
        def __init__(self):
            self.order_id = "o1"
            self.symbol = "BTCUSD"
            self.quantity = 1
            self.price = 100
        def as_dict(self):
            return {"order_id": self.order_id, "symbol": self.symbol, "quantity": self.quantity, "price": self.price}

    # also patch token factory to avoid external signer call
    re._token_factory = mock.MagicMock()
    re._token_factory.new_token.return_value = {"order_id": "o1"}

    res = re.submit_order(DummyOrder())
    assert res.get("status") == "filled"
    assert calls["n"] >= 3
