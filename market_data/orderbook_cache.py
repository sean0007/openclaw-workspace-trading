"""Lightweight L2 orderbook cache with snapshot and update helpers."""
from collections import defaultdict


class OrderbookCache:
    def __init__(self):
        # store price -> size for bids and asks
        self.bids = defaultdict(float)
        self.asks = defaultdict(float)

    def apply_snapshot(self, snapshot: dict):
        self.bids.clear()
        self.asks.clear()
        for p, s in snapshot.get("bids", []):
            self.bids[float(p)] = float(s)
        for p, s in snapshot.get("asks", []):
            self.asks[float(p)] = float(s)

    def apply_update(self, update: dict):
        for p, s in update.get("bids", []):
            p = float(p)
            s = float(s)
            if s == 0:
                self.bids.pop(p, None)
            else:
                self.bids[p] = s
        for p, s in update.get("asks", []):
            p = float(p)
            s = float(s)
            if s == 0:
                self.asks.pop(p, None)
            else:
                self.asks[p] = s

    def best_bid(self):
        if not self.bids:
            return None
        return max(self.bids.keys())

    def best_ask(self):
        if not self.asks:
            return None
        return min(self.asks.keys())

    def mid_price(self):
        b = self.best_bid()
        a = self.best_ask()
        if b is None or a is None:
            return None
        return (b + a) / 2.0
