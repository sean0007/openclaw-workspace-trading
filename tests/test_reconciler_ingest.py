from reconciler.reconciler import normalize_fill, reconcile


def test_normalize_and_reconcile():
    raw = {"price": "100.0", "qty": "2", "timestamp": 123456}
    n = normalize_fill(raw)
    assert n["price"] == 100.0
    assert n["qty"] == 2.0

    exec_journal = [{"qty": 2}]
    fills = [n]
    report = reconcile(exec_journal, fills)
    assert report["match"] is True
