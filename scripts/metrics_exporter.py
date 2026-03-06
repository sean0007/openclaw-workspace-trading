import re


SENSITIVE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in ["secret", "password", "token", "aws"]]


def scrub_metrics(text):
    lines = text.splitlines()
    out = []
    for ln in lines:
        safe = ln
        for pat in SENSITIVE_PATTERNS:
            safe = pat.sub("REDACTED", safe)
        out.append(safe)
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    data = sys.stdin.read()
    print(scrub_metrics(data))
#!/usr/bin/env python3
import os
import json
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, "artifacts")
os.makedirs(OUT_DIR, exist_ok=True)

def _ts():
    return datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ")

def export_per_strategy(strategy_id="default"):
    data = {
        "generated": _ts(),
        "strategy_id": strategy_id,
        "pnl": {"realized": 0.0, "unrealized": 0.0},
        "drawdown": 0.0,
        "slippage": 0.0,
        "fill_quality": 1.0,
    }
    path = os.path.join(OUT_DIR, f"per_strategy_{strategy_id}_{_ts()}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path

def export_portfolio():
    data = {
        "generated": _ts(),
        "pnl_drift": 0.0,
        "exposure": {"gross": 0.0, "net": 0.0},
        "var": 0.0,
    }
    path = os.path.join(OUT_DIR, f"portfolio_metrics_{_ts()}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path

def export_system_metrics():
    data = {
        "generated": _ts(),
        "risk_heartbeat": True,
        "market_data_freshness_sec": 0,
        "reconciliation_lag_sec": 0,
        "api_error_rate": 0.0,
    }
    path = os.path.join(OUT_DIR, f"system_metrics_{_ts()}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path

if __name__ == '__main__':
    print(export_per_strategy())
    print(export_portfolio())
    print(export_system_metrics())
