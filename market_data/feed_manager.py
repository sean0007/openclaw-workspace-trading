import time
import threading

"""Feed manager coordinating feeds, orderbook cache, candles, and validation."""
from .exchange_ws import ExchangeWebSocketSimulator
from .orderbook_cache import OrderbookCache
from .candle_builder import CandleBuilder
from .data_validator import validate_freshness


class FeedManager:
    def __init__(self, symbol=None):
        self.sources = []
        self.active = None
        self.lock = threading.Lock()
        self.alerts = []
        self.symbol = symbol
        self.feed = ExchangeWebSocketSimulator(symbol=self.symbol) if self.symbol else None
        self.ob = OrderbookCache()
        self.candle_builder = CandleBuilder(timeframe_seconds=60)

    def register(self, name, connect_fn, disconnect_fn=None):
        self.sources.append({"name": name, "connect": connect_fn, "disconnect": disconnect_fn})
        if self.active is None:
            self.active = name

    def simulate_disconnect(self, name):
        with self.lock:
            if self.active == name:
                # find next source
                for s in self.sources:
                    if s["name"] != name:
                        self.active = s["name"]
                        self.alerts.append({"type": "failover", "from": name, "to": self.active, "ts": time.time()})
                        return self.active
                # no fallback
                self.active = None
        return None

    def current(self):
        with self.lock:
            return self.active

    def get_alerts(self):
        return list(self.alerts)

    def poll_once(self):
        results = {"trades": [], "book": None, "candles": []}
        if not self.feed:
            return results
        for msg in self.feed.stream_once():
            if msg["type"] == "trade":
                if not validate_freshness(msg.get("ts"), max_age_seconds=10):
                    continue
                results["trades"].append(msg)
                candle = self.candle_builder.add_trade(msg)
                if candle:
                    results["candles"].append(candle)
            elif msg["type"] == "book":
                self.ob.apply_snapshot({"bids": msg.get("bids", []), "asks": msg.get("asks", [])})
                results["book"] = {"best_bid": self.ob.best_bid(), "best_ask": self.ob.best_ask(), "mid": self.ob.mid_price()}
        return results
