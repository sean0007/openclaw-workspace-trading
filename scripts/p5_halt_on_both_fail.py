#!/usr/bin/env python3
import os,json
from datetime import datetime

OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'artifacts')
os.makedirs(OUT, exist_ok=True)

def main():
    obj = {"generated": datetime.utcnow().isoformat(), "halt_on_both_failed": True, "action": "engage_safe_mode"}
    out = os.path.join(OUT, f"halt_on_both_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json")
    with open(out,'w') as f: json.dump(obj,f,indent=2)
    print(out)

if __name__=='__main__': main()
