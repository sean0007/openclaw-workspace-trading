#!/usr/bin/env python3
import os
import re
import json
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, "artifacts")
os.makedirs(OUT_DIR, exist_ok=True)

PATTERNS = {
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "aws_secret": re.compile(r"(?i)aws(.{0,10})?secret"),
    "hex_long": re.compile(r"\b[0-9a-fA-F]{32,}\b"),
    "private_key_begin": re.compile(r"-----BEGIN PRIVATE KEY-----"),
}

def scan():
    hits = []
    for dirpath, dirs, files in os.walk(ROOT):
        # skip artifacts, venv, caches and compiled dirs
        parts = dirpath.split(os.sep)
        if "artifacts" in parts or ".venv" in parts or "__pycache__" in parts or ".pytest_cache" in parts:
            continue
        for fn in files:
            path = os.path.join(dirpath, fn)
            # skip scanning the scanner source file itself
            if os.path.abspath(path) == os.path.abspath(__file__):
                continue
            try:
                with open(path, "r", errors="ignore") as f:
                    txt = f.read()
            except Exception:
                continue
            for name, pat in PATTERNS.items():
                for m in pat.finditer(txt):
                    hits.append({"file": os.path.relpath(path, ROOT), "pattern": name, "match": m.group(0)[:80]})
    return hits

def main():
    hits = scan()
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ")
    out = os.path.join(OUT_DIR, f"secret_scan_{ts}.json")
    with open(out, "w") as f:
        json.dump({"generated": ts, "hits": hits}, f, indent=2)
    print(out)
    if hits:
        print("FOUND", len(hits))

if __name__ == "__main__":
    main()
