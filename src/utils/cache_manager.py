import sqlite3
from pathlib import Path

class SizeCacheDB:
    def __init__(self):
        self.db_path = Path("cache/file_manager.db")
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""CREATE TABLE IF NOT EXISTS size_cache (
                        path TEXT PRIMARY KEY,
                        hash TEXT,
                        size INTEGER,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                      )""")
        conn.commit()
        conn.close()

    def update_cache(self, path, dir_hash, size):
        conn = sqlite3.connect(self.db_path)
        conn.execute("REPLACE INTO size_cache (path, hash, size) VALUES (?,?,?)",
                    (path, dir_hash, size))
        conn.commit()
        conn.close()

    def get_cache(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT path, hash, size FROM size_cache")
        return {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
