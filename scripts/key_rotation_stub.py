#!/usr/bin/env python3
"""
Minimal key rotation simulator for local testing. Writes rotated key entries to artifacts/.
In production this must integrate with secrets manager and exchange key APIs.
"""
import os
import json
import uuid
from datetime import datetime

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
os.makedirs(OUT_DIR, exist_ok=True)

def rotate(key_name):
    new = str(uuid.uuid4())
    artifact = {"rotated": datetime.utcnow().isoformat(), "key_name": key_name, "new_value": new}
    out_path = os.path.join(OUT_DIR, f"rotated_{key_name}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json")
    with open(out_path, "w") as f:
        json.dump(artifact, f)
    print(out_path)

if __name__ == '__main__':
    rotate(os.environ.get("ROTATE_KEY_NAME", "trading_key"))
