from market_data.feed_manager import FeedManager


def test_failover():
    fm = FeedManager()

    fm.register("primary", lambda: True)
    fm.register("secondary", lambda: True)

    assert fm.current() == "primary"

    fm.simulate_disconnect("primary")
    assert fm.current() == "secondary"
    alerts = fm.get_alerts()
    assert any(a["type"] == "failover" for a in alerts)
