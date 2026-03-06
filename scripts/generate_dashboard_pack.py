#!/usr/bin/env python3
import os
import json
from datetime import datetime

OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
os.makedirs(OUT, exist_ok=True)

def main():
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ")
    pack = {
        "generated": ts,
        "dashboards": [
            {"name": "strategy_overview", "url": "https://grafana.example/d/strategy"},
            {"name": "portfolio_health", "url": "https://grafana.example/d/portfolio"},
            {"name": "system_health", "url": "https://grafana.example/d/system"},
        ]
    }
    out = os.path.join(OUT, f"dashboard_pack_{ts}.json")
    with open(out, "w") as f:
        json.dump(pack, f, indent=2)
    print(out)

if __name__ == '__main__':
    main()
