#!/usr/bin/env python3
import os
import json
from datetime import datetime

OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
os.makedirs(OUT, exist_ok=True)

def main():
    trail = {"generated": datetime.utcnow().isoformat(), "entries": [{"event": "risk_check_pass", "order_id": "stub-order-1", "reason": "n/a"}]}
    out = os.path.join(OUT, f"risk_audit_trail_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json")
    with open(out, "w") as f:
        json.dump(trail, f, indent=2)
    print(out)

if __name__ == '__main__':
    main()
