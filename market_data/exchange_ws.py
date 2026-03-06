"""Simple exchange websocket simulator providing trade and book updates."""
import time
import random


class ExchangeWebSocketSimulator:
    """Simulates a simple feed producing trades and orderbook updates.

    Methods are synchronous and yield dict messages for simplicity in tests.
    """

    def __init__(self, symbol="BTCUSD"):
        self.symbol = symbol

    def stream_once(self):
        """Yield a single trade and a single book update."""
        ts = int(time.time())
        price = 30000.0 + random.uniform(-10, 10)
        trade = {"type": "trade", "symbol": self.symbol, "price": price, "size": random.uniform(0.001, 0.1), "ts": ts}
        book_update = {"type": "book", "symbol": self.symbol, "bids": [[price - 0.5, 1.0]], "asks": [[price + 0.5, 1.0]], "ts": ts}
        yield trade
        yield book_update
