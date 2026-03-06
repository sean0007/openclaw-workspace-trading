from market_data.data_validator import WatermarkValidator
import time


def test_freshness():
    v = WatermarkValidator()
    v.record("feed1", ts=time.time())
    assert not v.is_stale("feed1", max_age_seconds=1)

    # missing stream is stale
    assert v.is_stale("unknown_feed", max_age_seconds=1)
