#!/usr/bin/env python3
import os
import json
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, "artifacts")
os.makedirs(OUT_DIR, exist_ok=True)

def gather_state():
    # If a runtime state file exists, include it; otherwise produce a safe stub
    state = {
        "generated": datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ"),
        "strategy_id": os.getenv("STRATEGY_ID", "unknown"),
        "active": False,
        "positions": {},
        "open_orders": [],
        "notes": "Stub snapshot produced by automation. Replace with real runtime exporter in production.",
    }
    # Try to load a runtime state file if present
    possible = os.path.join(ROOT, "runtime", "strategy_state.json")
    if os.path.exists(possible):
        try:
            with open(possible, "r") as f:
                loaded = json.load(f)
            state.update({"active": True, "positions": loaded.get("positions", {}), "open_orders": loaded.get("open_orders", [])})
        except Exception:
            state["notes"] = "Failed to load runtime/state; stub kept."
    return state

def main():
    state = gather_state()
    ts = state["generated"].replace(":", "").replace("T", "_").replace("Z", "")
    out_path = os.path.join(OUT_DIR, f"strategy_state_{ts}.json")
    with open(out_path, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    print(out_path)

if __name__ == "__main__":
    main()
