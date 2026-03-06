import os
import time
import json
import urllib.request
import threading

import pytest

import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from risk_engine import RiskEngine, RiskException, ExecutionTokenFactory
from models import Order


def test_risk_engine_manual_override(monkeypatch):
    # prepare environment and a dummy token factory + fake execution response
    monkeypatch.setenv("WALLET_BALANCE", "100000")

    class DummyTokenFactory:
        def new_token(self, order_id):
            return {"order_id": order_id}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({"order_id": "ok", "status": "filled", "ts": int(time.time()), "pnl_change": 0}).encode()

    def _fake_urlopen(req, timeout=5):
        return _Resp()

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    re = RiskEngine(None)
    # inject dummy token factory to avoid network signer calls
    re._token_factory = DummyTokenFactory()

    # Engage kill switch via manual override (enable=False -> kill_switch True)
    re.manual_override(enable=False, actor="tester")
    with pytest.raises(RiskException, match="Kill switch is active"):
        re.submit_order(Order(symbol="BTCUSD", quantity=1, price=100))

    # Disable kill (enable=True) and ensure order now executes
    re.manual_override(enable=True, actor="tester")
    res = re.submit_order(Order(symbol="BTCUSD", quantity=1, price=100))
    assert res["status"] == "filled"


def test_execution_token_factory_requires_api_key(monkeypatch):
    # Ensure missing SIGNER_API_KEY causes RiskException on factory init
    monkeypatch.delenv("SIGNER_API_KEY", raising=False)
    monkeypatch.setenv("SIGNER_URL", "http://127.0.0.1:9000/sign")
    with pytest.raises(RiskException):
        ExecutionTokenFactory()
