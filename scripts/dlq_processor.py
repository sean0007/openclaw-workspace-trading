import sqlite3
import json
from pathlib import Path


DB = Path("artifacts/dlq.db")


def list_dlq():
    if not DB.exists():
        return []
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS dlq (id INTEGER PRIMARY KEY, payload TEXT)")
        cur.execute("SELECT id, payload FROM dlq ORDER BY id DESC LIMIT 100")
        return [{"id": r[0], "payload": json.loads(r[1])} for r in cur.fetchall()]


def mark_replayed(entry_id):
    # simple marker: remove entry
    if not DB.exists():
        return False
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM dlq WHERE id=?", (entry_id,))
        conn.commit()
    return True


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        print(json.dumps(list_dlq(), indent=2))
    else:
        cmd = sys.argv[1]
        if cmd == "list":
            print(json.dumps(list_dlq(), indent=2))
        elif cmd == "replay" and len(sys.argv) == 3:
            print(mark_replayed(int(sys.argv[2])))