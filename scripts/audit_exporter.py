from pathlib import Path
import time


def export_audit(name, data):
    p = Path("artifacts/audit")
    p.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    f = p / f"audit_{name}_{ts}.json"
    # write-once semantics: fail if exists
    if f.exists():
        raise RuntimeError("immutable file exists")
    f.write_text(data)
    return str(f)
