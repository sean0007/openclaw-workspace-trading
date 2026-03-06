import time
import random


def call_with_backoff(func, max_attempts=4, base_delay=0.1, max_delay=2.0, multiplier=2.0, jitter=0.1, retry_on=None):
    """Call `func()` with exponential backoff and jitter.

    Retries only when `retry_on(exc)` returns True. If `retry_on` is None,
    all exceptions are considered retryable (legacy behavior).

    `func` should raise an exception on failure. Returns func() result on success.
    """
    if retry_on is None:
        def retry_on(e):
            return True

    last_exc = None
    delay = base_delay
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except Exception as exc:
            last_exc = exc
            # If this exception is not retryable, propagate immediately
            try:
                should_retry = retry_on(exc)
            except Exception:
                should_retry = False
            if not should_retry:
                raise
            if attempt == max_attempts:
                raise
            # jitter
            j = random.uniform(0, jitter)
            sleep_s = min(max_delay, delay + j)
            time.sleep(sleep_s)
            delay = min(max_delay, delay * multiplier)
    raise last_exc
