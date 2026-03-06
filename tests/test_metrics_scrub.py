from scripts.metrics_exporter import scrub_metrics


def test_scrub():
    raw = "trading_requests_total{token=\"abc-secret\"} 1\nmy_metric 2"
    out = scrub_metrics(raw)
    assert "REDACTED" in out
    assert "secret" not in out.lower()
