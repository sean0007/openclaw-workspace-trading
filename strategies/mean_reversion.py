from collections import deque
from strategy_runtime.strategy_base import StrategyBase


class MeanReversionStrategy(StrategyBase):
    """Very small example mean-reversion strategy for testing.

    Keeps a short moving window of prices and emits a simple buy/sell
    signal when the current price deviates from the mean by a threshold.
    """

    def __init__(self, strategy_id: str, window=5, threshold=0.01):
        super().__init__(strategy_id)
        self.window = int(window)
        self.threshold = float(threshold)
        self.prices = deque(maxlen=self.window)
        self.last_signal = None

    def on_market_data(self, msg: dict):
        price = float(msg.get("price"))
        self.prices.append(price)
        if len(self.prices) < 2:
            return
        mean = sum(self.prices) / len(self.prices)
        if price > mean * (1 + self.threshold):
            self.last_signal = {"action": "sell", "price": price}
        elif price < mean * (1 - self.threshold):
            self.last_signal = {"action": "buy", "price": price}
        else:
            self.last_signal = {"action": "hold", "price": price}

    def on_signal(self, signal: dict):
        # no-op for now
        pass
