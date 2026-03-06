import time


class WatermarkValidator:
    def __init__(self):
        self.last_seen = {}

    def record(self, stream, ts=None):
        self.last_seen[stream] = ts or time.time()

    def is_stale(self, stream, max_age_seconds=5):
        ts = self.last_seen.get(stream)
        if ts is None:
            return True
        return (time.time() - ts) > max_age_seconds

    def summary(self):
        return {s: self.last_seen[s] for s in self.last_seen}


def validate_freshness(ts, max_age_seconds=5):
    if ts is None:
        return False
    try:
        return (int(time.time()) - int(ts)) <= int(max_age_seconds)
    except Exception:
        return False


def validate_cross_feed(p1, p2, tolerance=0.05):
    try:
        if p1 == 0:
            return False
        return abs(p1 - p2) / max(abs(p1), 1) <= tolerance
    except Exception:
        return False
"""Data validation helpers for market data integrity checks."""
import time


def validate_freshness(ts, max_age_seconds=5):
    now = int(time.time())
    try:
        ts_int = int(ts)
    except Exception:
        return False
    return abs(now - ts_int) <= int(max_age_seconds)


def validate_cross_feed(price_a, price_b, tolerance=0.01):
    """Return True if two feed prices are within `tolerance` fraction.

    tolerance=0.01 means 1%.
    """
    try:
        pa = float(price_a)
        pb = float(price_b)
    except Exception:
        return False
    if pa == 0 or pb == 0:
        return False
    diff = abs(pa - pb) / max(pa, pb)
    return diff <= float(tolerance)
