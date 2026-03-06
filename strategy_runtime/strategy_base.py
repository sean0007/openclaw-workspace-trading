import threading


class StrategyBase:
    """Base class for strategies. Implement `on_market_data` and `on_signal`.

    Subclasses should be lightweight and side-effect free; execution isolation
    is handled by the manager/worker.
    """

    def __init__(self, strategy_id: str):
        self.strategy_id = strategy_id
        self._running = False
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            self._running = True

    def stop(self):
        with self._lock:
            self._running = False

    def is_running(self) -> bool:
        with self._lock:
            return bool(self._running)

    def on_market_data(self, msg: dict):
        """Handle incoming market data message. Override in subclass."""
        raise NotImplementedError()

    def on_signal(self, signal: dict):
        """Handle a non-market signal (e.g., config change). Override."""
        raise NotImplementedError()
