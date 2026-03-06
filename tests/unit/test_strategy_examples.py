import time

from strategy_runtime.strategy_manager import StrategyManager
from strategies.mean_reversion import MeanReversionStrategy
from strategies.momentum_breakout import MomentumBreakoutStrategy


def test_strategy_manager_and_workers():
    mgr = StrategyManager()
    mr = MeanReversionStrategy("mr-1", window=3, threshold=0.01)
    mb = MomentumBreakoutStrategy("mb-1", threshold=0.01)
    mgr.register(mr)
    mgr.register(mb)
    mgr.start("mr-1")
    mgr.start("mb-1")

    # send a sequence of market ticks to exercise both strategies
    ticks = [
        {"price": 100.0, "ts": int(time.time())},
        {"price": 101.0, "ts": int(time.time())},
        {"price": 99.0, "ts": int(time.time())},
    ]
    for t in ticks:
        mgr.send_market("mr-1", t)
        mgr.send_market("mb-1", t)
        time.sleep(0.05)

    # allow background threads to process
    time.sleep(0.1)

    assert hasattr(mr, "last_signal")
    assert hasattr(mb, "last_signal")

    mgr.stop("mr-1")
    mgr.stop("mb-1")
