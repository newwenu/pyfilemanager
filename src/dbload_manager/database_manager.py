import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path="userdata\\db\\folder_size.db"):
        if not os.path.exists(db_path):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        """创建文件夹大小存储表"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS folder_sizes (
                path TEXT PRIMARY KEY,
                size TEXT NOT NULL,
                last_modified REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def get_cached_size(self, folder_path):
        """获取缓存的文件夹大小"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT size, last_modified FROM folder_sizes WHERE path = ?", (folder_path,))
        return cursor.fetchone()

    def update_cache(self, folder_path, size, last_modified):
        """更新缓存（插入或替换）"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO folder_sizes (path, size, last_modified) 
            VALUES (?, ?, ?)
        """, (folder_path, size, last_modified))
        self.conn.commit()

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
