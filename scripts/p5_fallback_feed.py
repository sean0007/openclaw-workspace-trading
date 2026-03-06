#!/usr/bin/env python3
import os, json
from datetime import datetime

OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'artifacts')
os.makedirs(OUT, exist_ok=True)

def main():
    obj = {"generated": datetime.utcnow().isoformat(), "primary":"ws://primary.feed","fallback":"https://fallback.rest","auto_failover":True}
    out = os.path.join(OUT, f"fallback_feed_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json")
    with open(out,'w') as f: json.dump(obj,f,indent=2)
    print(out)

if __name__=='__main__': main()
