#!/usr/bin/env python3
import os
import json
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, "artifacts")
os.makedirs(OUT_DIR, exist_ok=True)

def gather_pnl():
    # produce a minimal pnl snapshot
    return {
        "generated": datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ"),
        "pnls": {"strategy_overview": {"total_realized": 0.0, "total_unrealized": 0.0}},
    }

def gather_logs():
    # Try to collect recent git logs as proxy for recent activity
    try:
        import subprocess
        out = subprocess.check_output(["git", "-C", ROOT, "log", "-n", "20", "--pretty=format:%h %ad %s"], stderr=subprocess.DEVNULL, timeout=10)
        logs = out.decode().splitlines()
    except Exception:
        logs = ["No git logs available or git not present"]
    return logs

def main():
    data = gather_pnl()
    data["recent_logs"] = gather_logs()
    ts = data["generated"].replace(":", "").replace("T", "_").replace("Z", "")
    out_path = os.path.join(OUT_DIR, f"pnl_logs_{ts}.json")
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(out_path)

if __name__ == "__main__":
    main()
