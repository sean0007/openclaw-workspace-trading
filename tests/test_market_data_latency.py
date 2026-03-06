import time
from market_data.feed_manager import FeedManager


def test_latency_within_threshold():
    fm = FeedManager(symbol="BTCUSD")
    res = fm.poll_once()
    now = int(time.time())
    # If there are trades, they should be fresh (latency <= 5s)
    assert all((now - int(t["ts"]) <= 5) for t in res.get("trades", []))
