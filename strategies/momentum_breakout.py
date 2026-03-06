from strategy_runtime.strategy_base import StrategyBase


class MomentumBreakoutStrategy(StrategyBase):
    """Simple momentum breakout example.

    Emits a buy signal when price breaks above a small threshold over the last
    seen price, and sell when it breaks below.
    """

    def __init__(self, strategy_id: str, threshold=0.02):
        super().__init__(strategy_id)
        self.threshold = float(threshold)
        self.prev_price = None
        self.last_signal = None

    def on_market_data(self, msg: dict):
        price = float(msg.get("price"))
        if self.prev_price is None:
            self.prev_price = price
            return
        if price > self.prev_price * (1 + self.threshold):
            self.last_signal = {"action": "buy", "price": price}
        elif price < self.prev_price * (1 - self.threshold):
            self.last_signal = {"action": "sell", "price": price}
        else:
            self.last_signal = {"action": "hold", "price": price}
        self.prev_price = price

    def on_signal(self, signal: dict):
        pass
