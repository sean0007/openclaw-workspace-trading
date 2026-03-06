#!/usr/bin/env python3
import os
import json
from datetime import datetime

OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
os.makedirs(OUT, exist_ok=True)

def main():
    cfg = {
        "generated": datetime.utcnow().isoformat(),
        "gateway": "risk_gateway_stub",
        "routes": ["validate->signer->execute"],
        "status": "simulated"
    }
    out = os.path.join(OUT, f"risk_gateway_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json")
    with open(out, "w") as f:
        json.dump(cfg, f, indent=2)
    print(out)

if __name__ == '__main__':
    main()
