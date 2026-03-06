#!/usr/bin/env python3
import os
import json
import platform
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, "artifacts")
os.makedirs(OUT_DIR, exist_ok=True)

def gather():
    data = {
        "generated": datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ"),
        "platform": platform.platform(),
        "python": platform.python_version(),
    }
    # Docker inventory best-effort
    try:
        import subprocess
        out = subprocess.check_output(["docker", "ps", "--no-trunc"], stderr=subprocess.DEVNULL, timeout=10)
        data["docker_ps"] = out.decode().splitlines()
    except Exception:
        data["docker_ps"] = ["docker not available or access denied"]
    return data

def main():
    data = gather()
    ts = data["generated"].replace(":", "").replace("T", "_").replace("Z", "")
    out_path = os.path.join(OUT_DIR, f"runtime_inventory_{ts}.json")
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(out_path)

if __name__ == "__main__":
    main()
