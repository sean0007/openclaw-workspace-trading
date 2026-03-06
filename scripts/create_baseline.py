#!/usr/bin/env python3
import tarfile
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
FILES = [
    "MASTER_TRADING_DESK_PLAN.md",
    "todos.md",
    "README.md",
    "requirements.txt",
    "execution_service.py",
    "risk_engine.py",
    "models.py",
]

def main():
    ts = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir = os.path.join(ROOT, "artifacts")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"baseline_configs_{ts}.tar.gz")
    with tarfile.open(out_path, "w:gz") as tf:
        for fn in FILES:
            p = os.path.join(ROOT, fn)
            if os.path.exists(p):
                tf.add(p, arcname=fn)
    print(out_path)

if __name__ == "__main__":
    main()
