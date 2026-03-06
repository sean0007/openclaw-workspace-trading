#!/usr/bin/env python3
import os
import json
from datetime import datetime

OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
os.makedirs(OUT, exist_ok=True)

def main():
    alert = {"generated": datetime.utcnow().isoformat(), "alert": "DLQ_INSERTED", "detail": {"id": "dlq-stub-1", "reason": "simulated_failure"}}
    out = os.path.join(OUT, f"dlq_alert_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json")
    with open(out, "w") as f:
        json.dump(alert, f, indent=2)
    print(out)

if __name__ == '__main__':
    main()
