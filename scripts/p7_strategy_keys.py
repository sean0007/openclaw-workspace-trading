#!/usr/bin/env python3
import os,json
from datetime import datetime

OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'artifacts')
os.makedirs(OUT, exist_ok=True)

def main():
    obj = {"generated": datetime.utcnow().isoformat(), "strategy_keys": [{"strategy_id":"s1","key":"trading-key-s1"},{"strategy_id":"s2","key":"trading-key-s2"}]}
    out = os.path.join(OUT, f"strategy_keys_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json")
    with open(out,'w') as f: json.dump(obj,f,indent=2)
    print(out)

if __name__=='__main__': main()
