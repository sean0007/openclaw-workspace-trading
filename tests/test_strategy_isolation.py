import os
import sys
import time

# Ensure repo root is on sys.path for imports when tests run in CI
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from strategy_runtime.strategy_worker import run_strategy


def long_running():
    time.sleep(2)


def test_strategy_timeout():
    res = run_strategy(long_running, timeout=0.5)
    assert res.get("status") == "killed"
