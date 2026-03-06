#!/usr/bin/env python3
import sys
import subprocess
import platform
import json
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, "artifacts")
os.makedirs(OUT_DIR, exist_ok=True)

def pip_freeze():
    try:
        out = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], stderr=subprocess.STDOUT, timeout=30)
        return out.decode().splitlines()
    except Exception:
        return []

def main():
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ")
    data = {
        "generated": ts,
        "python": sys.version,
        "platform": platform.platform(),
        "pip_freeze": pip_freeze(),
    }
    out_path = os.path.join(OUT_DIR, f"dependencies_{ts}.json")
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(out_path)

if __name__ == "__main__":
    main()
