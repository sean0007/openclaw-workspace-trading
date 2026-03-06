#!/usr/bin/env python3
import os
import json
from datetime import datetime

OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
os.makedirs(OUT, exist_ok=True)

def main():
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ")
    data = {
        "generated": ts,
        "routes": {
            "discord": "disabled",
            "email": "ops@example.com",
            "pager": "+10000000000",
        },
        "status": "manual_bind_required"
    }
    out = os.path.join(OUT, f"alert_routing_{ts}.json")
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    print(out)

if __name__ == '__main__':
    from datetime import datetime
    main()
