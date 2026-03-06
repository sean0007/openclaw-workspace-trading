"""Build time-bucketed OHLCV candles from trade events."""
import time


class CandleBuilder:
    def __init__(self, timeframe_seconds=60):
        self.timeframe = int(timeframe_seconds)
        self._current_bucket = None
        self._open = None
        self._high = None
        self._low = None
        self._close = None
        self._volume = 0.0

    def _bucket_start(self, ts):
        return ts - (ts % self.timeframe)

    def add_trade(self, trade: dict):
        ts = int(trade.get("ts", time.time()))
        price = float(trade["price"])
        size = float(trade.get("size", 0.0))
        bucket = self._bucket_start(ts)
        if self._current_bucket is None:
            self._current_bucket = bucket
            self._open = self._high = self._low = price
            self._close = price
            self._volume = size
            return None
        if bucket == self._current_bucket:
            self._high = max(self._high, price)
            self._low = min(self._low, price)
            self._close = price
            self._volume += size
            return None
        # bucket rolled: emit candle for previous bucket
        candle = {
            "ts": self._current_bucket,
            "open": self._open,
            "high": self._high,
            "low": self._low,
            "close": self._close,
            "volume": self._volume,
        }
        # start new bucket
        self._current_bucket = bucket
        self._open = self._high = self._low = price
        self._close = price
        self._volume = size
        return candle
