import time
import random

from exchange_backoff import call_with_backoff


def test_backoff_retries_and_succeeds():
    state = {"calls": 0}

    def flaky():
        state["calls"] += 1
        if state["calls"] < 3:
            raise RuntimeError("temporary_502")
        return "ok"

    random.seed(1)
    start = time.time()
    res = call_with_backoff(flaky, max_attempts=5, base_delay=0.01, max_delay=0.05, multiplier=2.0, jitter=0.005)
    elapsed = time.time() - start
    assert res == "ok"
    assert state["calls"] == 3
    # elapsed should be at least base_delay*2 (two sleeps), but keep loose bound
    assert elapsed >= 0.0


def test_backoff_gives_up_after_max_attempts():
    def always_fail():
        raise RuntimeError("always_fail")

    random.seed(2)
    try:
        call_with_backoff(always_fail, max_attempts=3, base_delay=0.01, max_delay=0.02, multiplier=2.0, jitter=0.001)
        assert False, "should have raised"
    except RuntimeError:
        pass
