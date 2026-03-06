#!/usr/bin/env python3
import os
import json
from datetime import datetime

OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
os.makedirs(OUT, exist_ok=True)

def main():
    rules = {
        "generated": datetime.utcnow().isoformat(),
        "rules": [
            {"name": "per_asset_limit", "value": 250000},
            {"name": "leverage_limit", "value": 5.0},
            {"name": "daily_loss_cap", "value": 1000.0},
        ]
    }
    out = os.path.join(OUT, f"risk_checks_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json")
    with open(out, "w") as f:
        json.dump(rules, f, indent=2)
    print(out)

if __name__ == '__main__':
    main()
