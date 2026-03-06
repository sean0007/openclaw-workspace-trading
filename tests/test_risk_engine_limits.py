import os
import pytest

from risk_engine import RiskEngine, RiskException
from models import Order


def _make_engine(**kwargs):
    # Ensure signer API key exists for ExecutionTokenFactory init
    os.environ.setdefault("SIGNER_API_KEY", "test-signer-key")
    # Use a small wallet by default for leverage tests unless overridden
    os.environ.setdefault("WALLET_BALANCE", "100000")
    eng = RiskEngine(**kwargs)
    # Stub out network interactions: token creation and execution RPC
    eng._token_factory.new_token = lambda oid: "tok-test"
    eng._execute_with_bounded_retry = lambda order, payload: {"pnl_change": 0.0, "status": "ok"}
    return eng


def test_per_asset_limit_rejects():
    eng = _make_engine(per_asset_limit=100.0)
    # Create an order whose notional exceeds per_asset_limit
    order = Order(symbol="BTCUSD", quantity=2.0, price=60.0)
    with pytest.raises(RiskException):
        eng.submit_order(order)


def test_leverage_limit_rejects():
    # Low capital to trigger leverage cap
    os.environ["WALLET_BALANCE"] = "50"
    eng = _make_engine(leverage_limit=2.0)
    order = Order(symbol="ETHUSD", quantity=2.0, price=100.0)
    with pytest.raises(RiskException):
        eng.submit_order(order)


def test_invalid_order_values():
    eng = _make_engine()
    with pytest.raises(RiskException):
        eng.submit_order(Order(symbol="X", quantity=-1.0, price=10.0))
    with pytest.raises(RiskException):
        eng.submit_order(Order(symbol="X", quantity=1.0, price=0.0))


def test_missing_signer_api_key_causes_startup_failure(tmp_path, monkeypatch):
    # Ensure SIGNER_API_KEY missing triggers RiskException on init
    monkeypatch.delenv("SIGNER_API_KEY", raising=False)
    monkeypatch.delenv("WALLET_BALANCE", raising=False)
    with pytest.raises(RiskException):
        RiskEngine()
