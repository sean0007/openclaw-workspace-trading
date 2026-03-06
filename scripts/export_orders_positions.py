#!/usr/bin/env python3
import os
import json
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, "artifacts")
os.makedirs(OUT_DIR, exist_ok=True)

def gather():
    # Try to read runtime order/position snapshot if present
    stub = {
        "generated": datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ"),
        "positions": {},
        "open_orders": [],
        "notes": "Stub snapshot produced by automation. Replace with real runtime exporter in production.",
    }
    possible = os.path.join(ROOT, "runtime", "orders_positions.json")
    if os.path.exists(possible):
        try:
            with open(possible, "r") as f:
                data = json.load(f)
            stub.update(data)
        except Exception:
            stub["notes"] = "Failed to load runtime orders_positions; stub kept."
    return stub

def main():
    data = gather()
    ts = data["generated"].replace(":", "").replace("T", "_").replace("Z", "")
    out_path = os.path.join(OUT_DIR, f"orders_positions_{ts}.json")
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    print(out_path)

if __name__ == "__main__":
    main()
