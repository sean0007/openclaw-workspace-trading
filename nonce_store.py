import sqlite3
import threading
import os


class NonceStoreError(Exception):
    pass


class NonceStore:
    def insert_nonce(self, strategy_id: str, nonce: str, ts: int):
        raise NotImplementedError()


class SQLiteNonceStore(NonceStore):
    def __init__(self, path=None):
        self.path = path or os.getenv("EXECUTION_SERVICE_DB", "/tmp/execution_service_nonce.db")
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._ensure_schema()

    def _ensure_schema(self):
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS nonces (
                strategy_id TEXT NOT NULL,
                nonce TEXT NOT NULL,
                ts INTEGER NOT NULL,
                PRIMARY KEY(strategy_id, nonce)
            )
            """
        )
        self._conn.commit()

        rows = cur.execute("PRAGMA table_info('nonces')").fetchall()
        by_name = {row[1]: row for row in rows}
        needs_migration = (
            by_name.get("strategy_id", [None, None, None, 0])[3] != 1
            or by_name.get("nonce", [None, None, None, 0])[3] != 1
            or by_name.get("ts", [None, None, None, 0])[3] != 1
        )
        if not needs_migration:
            return

        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS nonces_new (
                strategy_id TEXT NOT NULL,
                nonce TEXT NOT NULL,
                ts INTEGER NOT NULL,
                PRIMARY KEY(strategy_id, nonce)
            )
            """
        )
        cur.execute(
            """
            INSERT OR IGNORE INTO nonces_new(strategy_id, nonce, ts)
            SELECT strategy_id, nonce, ts
            FROM nonces
            WHERE strategy_id IS NOT NULL AND nonce IS NOT NULL AND ts IS NOT NULL
            """
        )
        cur.execute("DROP TABLE nonces")
        cur.execute("ALTER TABLE nonces_new RENAME TO nonces")
        self._conn.commit()

    def insert_nonce(self, strategy_id: str, nonce: str, ts: int):
        with self._lock:
            try:
                cur = self._conn.cursor()
                cur.execute("BEGIN IMMEDIATE")
                cur.execute("INSERT INTO nonces(strategy_id, nonce, ts) VALUES (?, ?, ?)", (strategy_id, nonce, ts))
                self._conn.commit()
            except sqlite3.IntegrityError:
                self._conn.rollback()
                raise NonceStoreError("replayed_nonce")
            except Exception as exc:
                self._conn.rollback()
                raise NonceStoreError(f"nonce_store_error:{exc}")
