import multiprocessing
import time


def run_strategy(target_fn, args=(), timeout=5):
    """Run a strategy function in a separate process with timeout.

    Uses a direct process target so functions are pickleable when defined
    at module level.
    """
    p = multiprocessing.Process(target=target_fn, args=tuple(args))
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        return {"status": "killed"}
    return {"status": "ok"}
import threading
import queue
import time


class StrategyWorker(threading.Thread):
    """Runs a `StrategyBase` instance in a dedicated thread and delivers messages."""

    def __init__(self, strategy, name=None):
        super().__init__(name=name or f"worker-{strategy.strategy_id}")
        self.strategy = strategy
        self.inbox = queue.Queue()
        self._stop_event = threading.Event()
        self.daemon = True

    def run(self):
        self.strategy.start()
        while not self._stop_event.is_set():
            try:
                typ, payload = self.inbox.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                if typ == "market":
                    self.strategy.on_market_data(payload)
                elif typ == "signal":
                    self.strategy.on_signal(payload)
            except Exception:
                # Fail-safe: stop strategy on unhandled error
                try:
                    self.strategy.stop()
                except Exception:
                    pass
                self._stop_event.set()
        self.strategy.stop()

    def stop(self):
        self._stop_event.set()

    def send_market(self, msg: dict):
        self.inbox.put(("market", msg))

    def send_signal(self, sig: dict):
        self.inbox.put(("signal", sig))
