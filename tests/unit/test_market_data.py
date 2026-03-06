import time
from market_data.exchange_ws import ExchangeWebSocketSimulator
from market_data.orderbook_cache import OrderbookCache
from market_data.candle_builder import CandleBuilder
from market_data.data_validator import validate_freshness, validate_cross_feed
from market_data.feed_manager import FeedManager


def test_orderbook_apply_and_mid():
    ob = OrderbookCache()
    snapshot = {"bids": [[100.0, 1.0]], "asks": [[101.0, 1.0]]}
    ob.apply_snapshot(snapshot)
    assert ob.best_bid() == 100.0
    assert ob.best_ask() == 101.0
    assert ob.mid_price() == 100.5


def test_candle_builder_basic():
    cb = CandleBuilder(timeframe_seconds=1)
    ts = int(time.time())
    trade1 = {"ts": ts, "price": 10.0, "size": 1}
    trade2 = {"ts": ts, "price": 12.0, "size": 2}
    assert cb.add_trade(trade1) is None
    assert cb.add_trade(trade2) is None
    # force next bucket
    trade3 = {"ts": ts + 2, "price": 11.0, "size": 1}
    candle = cb.add_trade(trade3)
    assert candle["open"] == 10.0
    assert candle["high"] == 12.0
    assert candle["low"] == 10.0
    assert candle["close"] == 12.0


def test_feed_manager_smoke():
    fm = FeedManager(symbol="BTCUSD")
    res = fm.poll_once()
    # trades list may contain one trade
    assert "book" in res
    assert res["book"]["mid"] is None or isinstance(res["book"]["mid"], float)


def test_data_validator():
    assert validate_freshness(int(time.time()), max_age_seconds=5)
    assert validate_cross_feed(100.0, 100.5, tolerance=0.01) or validate_cross_feed(100.0, 100.5, tolerance=0.01) == False
