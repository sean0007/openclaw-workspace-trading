import os
import time
import uuid
import hmac
import hashlib
import threading
import logging
import json
import math
from collections import deque, defaultdict

import json
import urllib.request
import urllib.error
from exchange_backoff import call_with_backoff

# Execution now happens over RPC to a hardened ExecutionService. Read URL at call time
def _exec_service_url():
    return os.getenv("EXEC_SERVICE_URL", "http://127.0.0.1:8000/execute")

from models import Order

logger = logging.getLogger("risk_engine")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class RiskException(Exception):
    pass


def _log(event, **details):
    if not hasattr(_log, "_state"):
        _log._state = {"lock": threading.Lock(), "seq": 0, "prev_hash": "0" * 64}
    with _log._state["lock"]:
        _log._state["seq"] += 1
        payload = {
            "ts": time.time(),
            "event": event,
            "log_seq": _log._state["seq"],
            "log_prev_hash": _log._state["prev_hash"],
            **details,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        log_hash = hashlib.sha256(canonical.encode()).hexdigest()
        payload["log_hash"] = log_hash
        _log._state["prev_hash"] = log_hash
    logger.info(json.dumps(payload, sort_keys=True))


class ExecutionTokenFactory:
    """Creates HMAC-signed execution tokens that ExecutionEngine verifies.

    The shared secret must be supplied via environment variable
    `RISK_EXECUTOR_SHARED_SECRET` to avoid hardcoding.
    """

    def __init__(self):
        # RiskEngine no longer holds signing keys. It requests tokens from a Signer service.
        self.signer_url = os.getenv("SIGNER_URL", "http://127.0.0.1:9000/sign")
        self.signer_api_key = os.getenv("SIGNER_API_KEY")
        # By default require `SIGNER_API_KEY`. Optionally allow a local
        # fallback token generator when the operator explicitly enables it
        # via `OPENCLAW_ALLOW_LOCAL_SIGNER=true` (for local dev only).
        allow_fallback = os.getenv("OPENCLAW_ALLOW_LOCAL_SIGNER", "false").lower() in ("1", "true", "yes")
        if not self.signer_api_key:
            if allow_fallback:
                _log("signer_key_missing", note="falling_back_to_local_token_generator")
                self._local_fallback = True
            else:
                raise RiskException("Missing SIGNER_API_KEY env var for token requests")
        else:
            self._local_fallback = False

    def new_token(self, order_id: str):
        # If running without a configured signer, return a deterministic
        # local token structure suitable for tests and local runs. This
        # token is NOT cryptographically signed and should NOT be used in
        # production where the ExecutionService verifies tokens.
        strategy_id = os.getenv("STRATEGY_ID", "unknown")
        if getattr(self, "_local_fallback", False):
            now = int(time.time())
            token = {
                "order_id": order_id,
                "timestamp": now,
                "nonce": str(uuid.uuid4()),
                "expiry": now + 60,
                "strategy_id": strategy_id,
                "sig": "local-fallback"
            }
            return token

        # Request a signed token from Signer service
        payload = json.dumps({"order_id": order_id, "strategy_id": strategy_id}).encode()
        req = urllib.request.Request(self.signer_url, data=payload, headers={"Content-Type": "application/json", "X-API-KEY": self.signer_api_key})
        try:
            with urllib.request.urlopen(req, timeout=2) as resp:
                body = resp.read()
                obj = json.loads(body)
                return obj["token"]
        except Exception as e:
            raise RiskException(f"failed_to_get_token:{str(e)}")


class RiskEngine:
    def __init__(self,
                 execution_engine=None,
                 daily_loss_cap: float = 1000.0,
                 gross_exposure_limit: float = 1_000_000.0,
                 net_exposure_limit: float = 500_000.0,
                 per_asset_limit: float = 250_000.0,
                 leverage_limit: float = 5.0,
                 trade_frequency_limit: int = 100,
                 trade_window_seconds: int = 60,
                 circuit_atr_threshold: float = None,
                 wallet_balance_provider=None,
                 ): 
        self._exec = execution_engine
        self._token_factory = ExecutionTokenFactory()
        # heartbeat monitoring
        self._heartbeat_lock = threading.Lock()
        self._heartbeat_last = time.time()
        self._heartbeat_monitor_thread = None
        self._heartbeat_monitor_stop = threading.Event()
        self.max_data_age_seconds = None

        # Enforcement params
        self.daily_loss_cap = daily_loss_cap
        self.gross_exposure_limit = gross_exposure_limit
        self.net_exposure_limit = net_exposure_limit
        self.per_asset_limit = per_asset_limit
        self.leverage_limit = leverage_limit
        self.trade_frequency_limit = trade_frequency_limit
        self.trade_window_seconds = trade_window_seconds
        self.circuit_atr_threshold = circuit_atr_threshold
        self.wallet_balance_provider = wallet_balance_provider
        self.minimum_wallet_balance = float(os.getenv("MIN_WALLET_BALANCE", "1e-6"))

        # Runtime state
        self._pnl = 0.0
        self._pnl_date = time.strftime("%Y-%m-%d")
        self._positions = defaultdict(float)
        self._notional = 0.0
        self._trade_timestamps = deque()
        self._asset_trade_timestamps = defaultdict(deque)
        self._kill_switch = False
        self._kill_lock = threading.Lock()
        self._state_lock = threading.RLock()
        self.exec_rpc_max_attempts = max(1, int(os.getenv("EXEC_RPC_MAX_ATTEMPTS", "2")))
        self.exec_rpc_retry_backoff_seconds = float(os.getenv("EXEC_RPC_RETRY_BACKOFF_SECONDS", "0.15"))
        self.exec_rpc_retry_backoff_max_seconds = float(os.getenv("EXEC_RPC_RETRY_BACKOFF_MAX_SECONDS", "2.0"))
        self.exec_rpc_retry_backoff_multiplier = float(os.getenv("EXEC_RPC_RETRY_BACKOFF_MULTIPLIER", "2.0"))
        self._startup_wallet_preflight_check()

    # --- Public API ---
    def submit_order(self, order: Order, signal: str = None):
        _log("signal_received", signal=signal, order=order.as_dict())
        # Fail-closed: any internal issue must not result in execution
        try:
            with self._state_lock:
                if self._kill_switch:
                    _log("rejected", reason="kill_switch_active", order=order.as_dict())
                    raise RiskException("Kill switch is active")

                self._validate_order_inputs(order)
                self._preflight_wallet_balance(order)
                self._reset_daily_if_needed()
                self._enforce_trade_frequency(order)
                self._enforce_exposure(order)
                self._enforce_leverage(order)
                self._enforce_daily_loss_cap()
                self._enforce_circuit(order)
                # Validate market data freshness before proceeding
                self._validate_market_freshness(order)
                self._validate_capital_at_risk(order)

                token = self._token_factory.new_token(order.order_id)
                _log("approved", order=order.as_dict())

                payload = json.dumps({"token": token, "order": order.as_dict()}).encode()
                _log("pre_execution", order=order.as_dict())
                result = self._execute_with_bounded_retry(order, payload)

                _log("executed", order=order.as_dict(), result=result)
                self._update_state_after_fill(order, result)
                return result

        except Exception as e:
            _log("rejection", reason=str(e), order=order.as_dict())
            # Fail-closed: always raise so callers cannot assume execution
            raise

    def _execute_with_bounded_retry(self, order: Order, payload: bytes):
        exec_url = _exec_service_url()

        def attempt_call():
            req = urllib.request.Request(exec_url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read()
                return body

        try:
            _log("execution_attempt", max_attempts=self.exec_rpc_max_attempts, order_id=order.order_id)
            # Only retry on transient HTTP errors (429, 5xx) or non-HTTP errors (network issues).
            def _retry_on(exc):
                # urllib HTTPError has `.code`
                try:
                    import urllib.error as _urlerr
                except Exception:
                    _urlerr = None
                if _urlerr and isinstance(exc, _urlerr.HTTPError):
                    # Retry only on rate-limit or server errors
                    return exc.code in (429, 500, 502, 503, 504)
                # For other exception types (e.g., URLError, socket errors) allow retry
                return True

            body = call_with_backoff(
                attempt_call,
                max_attempts=self.exec_rpc_max_attempts,
                base_delay=self.exec_rpc_retry_backoff_seconds,
                max_delay=self.exec_rpc_retry_backoff_max_seconds,
                multiplier=self.exec_rpc_retry_backoff_multiplier,
                jitter=0.05,
                retry_on=_retry_on,
            )
            _log("execution_latency", order_id=order.order_id, attempt_ts=int(time.time()))
            return json.loads(body)
        except urllib.error.HTTPError as he:
            _log("rejection", reason=f"rpc_http_error:{he.code}", order=order.as_dict())
            raise RiskException("ExecutionService rejected the order")
        except Exception as exc:
            _log("rejection", reason=f"rpc_failure:{str(exc)}", order=order.as_dict())
            raise RiskException("ExecutionService unreachable or failed")

    # --- Enforcement primitives ---
    def _reset_daily_if_needed(self):
        today = time.strftime("%Y-%m-%d")
        if self._pnl_date != today:
            _log("daily_reset", previous_date=self._pnl_date, new_date=today, pnl=self._pnl)
            self._pnl = 0.0
            self._pnl_date = today

    def _enforce_daily_loss_cap(self):
        if self.daily_loss_cap is not None and self._pnl <= -abs(self.daily_loss_cap):
            self._activate_kill("daily_loss_cap_breached")
            raise RiskException("Daily loss cap breached")

    def _enforce_exposure(self, order: Order):
        projected_asset = abs(self._positions[order.symbol] + order.quantity * order.price)
        if projected_asset > self.per_asset_limit:
            raise RiskException("Per-asset exposure limit exceeded")

        projected_notional = self._notional + abs(order.quantity * order.price)
        if projected_notional > self.gross_exposure_limit:
            raise RiskException("Gross exposure limit exceeded")

        projected_net = abs(sum(self._positions.values()) + order.quantity * order.price)
        if projected_net > self.net_exposure_limit:
            raise RiskException("Net exposure limit exceeded")

    def _enforce_leverage(self, order: Order):
        if self.leverage_limit is None:
            return
        projected_notional = self._notional + abs(order.quantity * order.price)
        capital = self._get_capital()
        if capital <= self.minimum_wallet_balance:
            raise RiskException("Insufficient wallet balance")
        projected_leverage = projected_notional / capital
        if projected_leverage > self.leverage_limit:
            raise RiskException("Leverage limit exceeded")

    def _enforce_trade_frequency(self, order: Order):
        now = time.time()
        self._trade_timestamps.append(now)
        while self._trade_timestamps and now - self._trade_timestamps[0] > self.trade_window_seconds:
            self._trade_timestamps.popleft()
        if len(self._trade_timestamps) > self.trade_frequency_limit:
            raise RiskException("Trade frequency exceeded")

        asset_q = self._asset_trade_timestamps[order.symbol]
        asset_q.append(now)
        while asset_q and now - asset_q[0] > self.trade_window_seconds:
            asset_q.popleft()
        if len(asset_q) > self.trade_frequency_limit:
            raise RiskException("Asset trade frequency exceeded")

    def _enforce_circuit(self, order: Order):
        # Very simple ATR threshold-based freeze: if configured and price move large
        if self.circuit_atr_threshold is None:
            return
        # Placeholder: In production this must consult market ATR series
        if abs(order.quantity * order.price) > self.circuit_atr_threshold:
            self._activate_kill("circuit_breaker_triggered")
            raise RiskException("Circuit breaker triggered")

    def _validate_capital_at_risk(self, order: Order):
        # Capital at risk = abs(notional of order) / capital
        capital = self._get_capital()
        if capital <= self.minimum_wallet_balance:
            raise RiskException("Insufficient wallet balance")
        car = abs(order.quantity * order.price) / capital
        if car > 0.5:
            raise RiskException("Capital-at-risk exceeds allowed fraction")

    def _get_capital(self):
        if self.wallet_balance_provider is not None:
            balance = self.wallet_balance_provider()
        else:
            balance = os.getenv("WALLET_BALANCE", "100000")
        try:
            value = float(balance)
        except (TypeError, ValueError):
            raise RiskException("Invalid wallet balance source")
        if not math.isfinite(value) or value < 0:
            raise RiskException("Invalid wallet balance source")
        return value

    def _validate_order_inputs(self, order: Order):
        if not math.isfinite(order.quantity) or not math.isfinite(order.price):
            raise RiskException("Invalid order values")
        if order.quantity <= 0 or order.price <= 0:
            raise RiskException("Order quantity and price must be positive")

    def _preflight_wallet_balance(self, order: Order):
        balance = self._get_capital()
        required_notional = abs(order.quantity * order.price)
        _log(
            "wallet_preflight",
            order_id=order.order_id,
            wallet_balance=balance,
            required_notional=required_notional,
            min_wallet_balance=self.minimum_wallet_balance,
        )
        if balance <= self.minimum_wallet_balance:
            raise RiskException("Insufficient wallet balance")
        if required_notional > balance:
            raise RiskException("Insufficient wallet balance for order notional")

    def _startup_wallet_preflight_check(self):
        if not math.isfinite(self.minimum_wallet_balance) or self.minimum_wallet_balance < 0:
            _log("wallet_preflight_config_invalid", reason="invalid_min_wallet_balance", min_wallet_balance=self.minimum_wallet_balance)
            raise RiskException("Invalid MIN_WALLET_BALANCE configuration")

        balance = self._get_capital()
        status = "ok" if balance > self.minimum_wallet_balance else "near_zero"
        _log(
            "wallet_preflight_config_valid",
            wallet_balance=balance,
            min_wallet_balance=self.minimum_wallet_balance,
            status=status,
        )

    def _activate_kill(self, reason: str):
        with self._kill_lock:
            self._kill_switch = True
            _log("kill_activated", reason=reason)
        # Attempt to notify the execution gateway to set its risk lock state.
        try:
            gateway_url = os.getenv("EXEC_GATEWAY_RISK_URL", "http://127.0.0.1:8000/risk/lock")
            secret = os.getenv("RISK_CIRCUIT_SHARED_SECRET")
            if not secret:
                _log("risk_notify_skipped", reason="no_shared_secret_configured")
                return
            data = json.dumps({"lock": True, "reason": reason, "actor": "risk_engine"}).encode()
            req = urllib.request.Request(gateway_url, data=data, headers={"Content-Type": "application/json", "X-RISK-SHARED-SECRET": secret})
            with urllib.request.urlopen(req, timeout=2) as resp:
                _log("risk_notify_sent", reason=reason, gateway=gateway_url, code=resp.getcode())
        except Exception as exc:
            _log("risk_notify_failed", reason=str(exc))

    # --- Heartbeat monitor helpers ---
    def start_heartbeat_monitor(self, interval_seconds=1.0, timeout_seconds=60.0):
        self.max_heartbeat_timeout = timeout_seconds
        self._heartbeat_monitor_stop.clear()

        def monitor():
            while not self._heartbeat_monitor_stop.is_set():
                with self._heartbeat_lock:
                    last = self._heartbeat_last
                if time.time() - last > self.max_heartbeat_timeout:
                    _log("heartbeat_timeout_detected", last_seen=last)
                    try:
                        self._activate_kill("heartbeat_timeout")
                    except Exception:
                        pass
                    break
                time.sleep(interval_seconds)

        self._heartbeat_monitor_thread = threading.Thread(target=monitor, daemon=True)
        self._heartbeat_monitor_thread.start()

    def stop_heartbeat_monitor(self):
        if self._heartbeat_monitor_thread:
            self._heartbeat_monitor_stop.set()
            self._heartbeat_monitor_thread.join(timeout=2)

    def heartbeat_ping(self):
        with self._heartbeat_lock:
            self._heartbeat_last = time.time()

    def set_market_data_provider(self, provider_callable, max_age_seconds=10):
        self.market_data_provider = provider_callable
        self.max_data_age_seconds = max_age_seconds

    def _validate_market_freshness(self, order: Order):
        if getattr(self, "market_data_provider", None) is None or self.max_data_age_seconds is None:
            return
        ts = self.market_data_provider(order.symbol)
        if ts is None:
            return
        if time.time() - ts > self.max_data_age_seconds:
            self._activate_kill("stale_market_data")
            raise RiskException("stale_market_data")

    def manual_override(self, enable: bool, actor: str):
        with self._kill_lock:
            # Manual override must be logged and controlled
            self._kill_switch = not enable
            _log("manual_override", actor=actor, enabled=enable)

    def _update_state_after_fill(self, order: Order, result: dict):
        # Update positions, notional, and pnl tracking conservatively
        fill_notional = order.quantity * order.price
        self._positions[order.symbol] += fill_notional
        self._notional = sum(abs(v) for v in self._positions.values())
        # Simulated PnL update (in a real system we'd use executed price vs mark)
        self._pnl += result.get("pnl_change", 0.0)
