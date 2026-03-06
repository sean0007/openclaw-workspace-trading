#!/usr/bin/env python3
import os
import json
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, "artifacts")
os.makedirs(OUT_DIR, exist_ok=True)

def generate_alert_rules():
    rules = {
        "generated": datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ"),
        "alerts": [
            {"name": "risk_heartbeat_missing", "severity": "critical", "expr": "risk_heartbeat == false"},
            {"name": "market_data_stale", "severity": "critical", "expr": "market_data_freshness_sec > 5"},
            {"name": "execution_blocked", "severity": "high", "expr": "execution_blocked == true"},
        ],
    }
    out = os.path.join(OUT_DIR, f"alert_rules_{rules['generated']}.json")
    with open(out, "w") as f:
        json.dump(rules, f, indent=2)
    return out

if __name__ == '__main__':
    print(generate_alert_rules())
