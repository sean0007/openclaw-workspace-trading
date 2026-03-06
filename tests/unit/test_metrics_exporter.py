import os
from scripts import metrics_exporter, alert_rules


def test_export_per_strategy(tmp_path):
    path = metrics_exporter.export_per_strategy("teststrat")
    assert os.path.exists(path)
    with open(path, "r") as f:
        data = f.read()
    assert "strategy_id" in data


def test_export_portfolio():
    path = metrics_exporter.export_portfolio()
    assert os.path.exists(path)
    with open(path) as f:
        txt = f.read()
    assert "pnl_drift" in txt


def test_export_system_metrics():
    path = metrics_exporter.export_system_metrics()
    assert os.path.exists(path)
    with open(path) as f:
        txt = f.read()
    assert "risk_heartbeat" in txt


def test_generate_alert_rules():
    path = alert_rules.generate_alert_rules()
    assert os.path.exists(path)
    with open(path) as f:
        txt = f.read()
    assert "alerts" in txt


def test_impact_estimator_script_creates_artifact():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    scripts_dir = os.path.join(repo_root, 'scripts')
    script = os.path.join(scripts_dir, 'p8_impact_estimator.py')
    assert os.path.exists(script)
    import subprocess
    res = subprocess.run(['python3', script], capture_output=True, text=True)
    assert res.returncode == 0
    path = res.stdout.strip()
    assert os.path.exists(path)
