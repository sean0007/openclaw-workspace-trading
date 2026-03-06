#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def validate(path):
    p = Path(path).expanduser()
    if not p.exists():
        print(f"MISSING: {p}")
        return 2
    try:
        data = json.loads(p.read_text())
    except Exception as e:
        print(f"INVALID JSON: {e}")
        return 3
    # Minimal schema checks
    if 'gateway' not in data:
        print('MISSING_KEY: gateway')
        return 4
    gw = data['gateway']
    if 'mode' not in gw:
        print('MISSING_KEY: gateway.mode')
        return 5
    print('OK')
    return 0

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else str(Path('~/.openclaw/openclaw.json').expanduser())
    rc = validate(path)
    sys.exit(rc)
