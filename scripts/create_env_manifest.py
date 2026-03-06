#!/usr/bin/env python3
import os
import json
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, "artifacts")
os.makedirs(OUT_DIR, exist_ok=True)

def redact(val: str) -> str:
    if val is None:
        return None
    # keep first and last 2 chars for short tokens, else redact middle
    if len(val) <= 6:
        return "REDACTED"
    return val[:2] + "*" * (len(val) - 4) + val[-2:]

def main():
    keys = sorted(os.environ.keys())
    manifest = {}
    for k in keys:
        # redact values for all keys
        manifest[k] = redact(os.environ.get(k))

    ts = datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ")
    out_path = os.path.join(OUT_DIR, f"env_manifest_{ts}.json")
    with open(out_path, "w") as f:
        json.dump({"generated": ts, "vars": manifest}, f, indent=2, sort_keys=True)
    print(out_path)

if __name__ == "__main__":
    main()
