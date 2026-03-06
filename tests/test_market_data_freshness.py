import time
from market_data.feed_manager import FeedManager


class OldFeed:
    def __init__(self, symbol="BTCUSD"):
        self.symbol = symbol

    def stream_once(self):
        ts = int(time.time()) - 1000
        trade = {"type": "trade", "symbol": self.symbol, "price": 100.0, "size": 1.0, "ts": ts}
        book = {"type": "book", "symbol": self.symbol, "bids": [[99.0, 1.0]], "asks": [[101.0, 1.0]], "ts": ts}
        yield trade
        yield book


def test_freshness_filters_old_trades():
    fm = FeedManager(symbol="BTCUSD")
    fm.feed = OldFeed()
    res = fm.poll_once()
    # old trades should be filtered out by freshness check
    assert res.get("trades") == []
    # orderbook snapshot should still be applied
    assert res.get("book") is not None
