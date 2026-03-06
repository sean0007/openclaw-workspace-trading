#!/usr/bin/env python3
import os
import sqlite3
from datetime import datetime

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
os.makedirs(OUT_DIR, exist_ok=True)
DB = os.path.join(OUT_DIR, "dlq.db")

def main():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS dlq (id TEXT PRIMARY KEY, reason TEXT, payload TEXT, ts TEXT)")
    c.execute("INSERT OR IGNORE INTO dlq (id, reason, payload, ts) VALUES (?, ?, ?, ?)", ("dlq-stub-1", "simulated_failure", "{}", datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    print(DB)

if __name__ == '__main__':
    main()
