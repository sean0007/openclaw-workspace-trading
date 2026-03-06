"""Simple strategy manager to register, start, stop, and route data to strategies."""
import threading
import logging
from typing import Dict

from .strategy_worker import StrategyWorker

logger = logging.getLogger("strategy_manager")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class StrategyManager:
    def __init__(self, isolation_mode: str = "inproc"):
        # isolation_mode currently supports 'inproc' (placeholder for future 'process' or 'container')
        self.isolation_mode = isolation_mode
        self._workers: Dict[str, StrategyWorker] = {}
        self._lock = threading.RLock()

    def register(self, strategy):
        with self._lock:
            sid = strategy.strategy_id
            if sid in self._workers:
                raise RuntimeError("strategy_already_registered")
            w = StrategyWorker(strategy)
            self._workers[sid] = w
            logger.info(f"registered strategy {sid}")

    def start(self, strategy_id: str):
        with self._lock:
            w = self._workers.get(strategy_id)
            if not w:
                raise RuntimeError("strategy_not_found")
            if not w.is_alive():
                w.start()
                logger.info(f"started strategy {strategy_id}")

    def stop(self, strategy_id: str):
        with self._lock:
            w = self._workers.get(strategy_id)
            if not w:
                return
            w.stop()
            logger.info(f"stopped strategy {strategy_id}")

    def send_market(self, strategy_id: str, msg: dict):
        with self._lock:
            w = self._workers.get(strategy_id)
            if not w:
                raise RuntimeError("strategy_not_found")
            w.send_market(msg)

    def broadcast_market(self, msg: dict):
        with self._lock:
            for w in list(self._workers.values()):
                w.send_market(msg)

    def list_strategies(self):
        with self._lock:
            return list(self._workers.keys())
