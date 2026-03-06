#!/usr/bin/env python3
import os
import sqlite3
from datetime import datetime

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
os.makedirs(OUT_DIR, exist_ok=True)
DB = os.path.join(OUT_DIR, "idempotency_journal.db")

def main():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS journal (order_id TEXT PRIMARY KEY, nonce TEXT, timestamp TEXT, strategy_id TEXT)")
    c.execute("INSERT OR IGNORE INTO journal (order_id, nonce, timestamp, strategy_id) VALUES (?, ?, ?, ?)", ("stub-order-1", "nonce-1", datetime.utcnow().isoformat(), "stub-strat"))
    conn.commit()
    conn.close()
    print(DB)

if __name__ == '__main__':
    main()
