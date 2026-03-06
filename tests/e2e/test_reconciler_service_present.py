import os


def test_reconciler_service_present():
    # Expect a reconciler service entry-point for production reconciliation
    path = os.path.join("reconciler", "reconciler_service.py")
    assert os.path.exists(path), f"Reconciler service missing: {path}"
