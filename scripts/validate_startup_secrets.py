#!/usr/bin/env python3
import os
import sys
import json

REQUIRED = [
    "SIGNER_API_KEY",
    "EXECUTION_OPERATOR_API_KEY",
    "RISK_EXECUTOR_SHARED_SECRET",
]

def main():
    missing = [k for k in REQUIRED if not os.environ.get(k)]
    out = {"ok": len(missing) == 0, "missing": missing}
    print(json.dumps(out))
    if missing:
        sys.exit(2)

if __name__ == "__main__":
    main()
