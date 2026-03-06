#!/usr/bin/env python3
import os
import sqlite3
from datetime import datetime

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
os.makedirs(OUT_DIR, exist_ok=True)
DB = os.path.join(OUT_DIR, "execution_queue.db")

def main():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS queue (id TEXT PRIMARY KEY, payload TEXT, created_ts TEXT)")
    # insert a stub row
    c.execute("INSERT OR IGNORE INTO queue (id, payload, created_ts) VALUES (?, ?, ?)", ("stub-1", "{}", datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    print(DB)

if __name__ == '__main__':
    main()
