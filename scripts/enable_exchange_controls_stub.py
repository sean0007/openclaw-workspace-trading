#!/usr/bin/env python3
"""
Stub to document and simulate enabling exchange-side controls.
In production this requires operator console actions; this script emits the steps to perform.
"""
import json
from datetime import datetime

def main():
    steps = [
        "Ensure IP allowlist contains operator IPs only",
        "Disable withdrawal permissions for trading keys",
        "Create scoped trading-only API keys per strategy/subaccount",
        "Enable 2FA and rotation schedule for high-privilege keys",
    ]
    out = {"generated": datetime.utcnow().isoformat(), "steps": steps, "status": "manual_action_required"}
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    main()
