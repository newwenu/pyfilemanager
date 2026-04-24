"""
文件树数据库管理器 - 路径枚举模型

支持存储：
- 文件/文件夹基本信息
- 文件夹大小（预先计算）
- 子文件夹修改时间（用于快速判断缓存有效性）
- 文件夹内容哈希（用于检测变化）
"""

import sqlite3
import hashlib
import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Set
from dataclasses import dataclass
from contextlib import contextmanager
import threading


@dataclass
class FileNode:
    """文件/文件夹节点数据类"""
    path: str
    name: str
    parent_path: Optional[str]
    depth: int
    is_dir: bool
    size: int = 0  # 文件大小或文件夹总大小
    mtime: float = 0.0  # 修改时间
    file_count: int = 0  # 文件夹内文件数
    folder_count: int = 0  # 文件夹内子文件夹数
    content_hash: Optional[str] = None  # 内容哈希（用于检测变化）
    updated_at: float = 0.0


class FileTreeDatabase:
    """
    文件树数据库管理器
    
    使用路径枚举模型存储文件树，支持：
    1. 快速查询子树（LIKE前缀匹配）
    2. 预存文件夹大小和统计信息
    3. 内容哈希检测变化
    4. 批量操作优化
    """
    
    def __init__(self, db_path: str = "userdata/db/file_tree.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 线程本地存储
        self._local = threading.local()
        
        # 初始化数据库
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        """获取线程专用连接"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            # 性能优化
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn.execute("PRAGMA cache_size=10000")
            self._local.conn.execute("PRAGMA temp_store=MEMORY")
            # 启用内存映射 I/O（加速读取）
            # 设置为 256MB，如果数据库更大，SQLite 会自动处理
            self._local.conn.execute("PRAGMA mmap_size=268435456")
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_db(self):
        """初始化数据库表结构"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 主表：文件树节点
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_tree (
                path TEXT PRIMARY KEY,
                parent_path TEXT,
                name TEXT NOT NULL,
                depth INTEGER NOT NULL,
                is_dir BOOLEAN NOT NULL DEFAULT 0,
                size INTEGER DEFAULT 0,           -- 文件大小或文件夹总大小
                mtime REAL DEFAULT 0,             -- 修改时间
                file_count INTEGER DEFAULT 0,     -- 文件夹内文件数
                folder_count INTEGER DEFAULT 0,   -- 文件夹内子文件夹数
                content_hash TEXT,                -- 内容哈希（检测变化）
                updated_at REAL DEFAULT (unixepoch()),
                
                FOREIGN KEY (parent_path) REFERENCES file_tree(path) ON DELETE CASCADE
            )
        """)
        
        # 索引优化
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parent ON file_tree(parent_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_dir ON file_tree(is_dir)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_depth ON file_tree(depth)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mtime ON file_tree(mtime)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_updated ON file_tree(updated_at)")
        
        # 文件夹大小缓存表（专门用于快速查询）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS folder_size_cache (
                path TEXT PRIMARY KEY,
                size INTEGER NOT NULL,            -- 总大小（字节）
                file_count INTEGER DEFAULT 0,     -- 文件数量
                folder_count INTEGER DEFAULT 0,   -- 子文件夹数量
                mtime REAL NOT NULL,              -- 文件夹修改时间
                content_hash TEXT,                -- 内容哈希
                last_scan_time REAL,              -- 上次扫描时间
                scan_duration_ms INTEGER,         -- 扫描耗时（毫秒）
                updated_at REAL DEFAULT (unixepoch()),
                
                FOREIGN KEY (path) REFERENCES file_tree(path) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_size_mtime ON folder_size_cache(mtime)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_size_updated ON folder_size_cache(updated_at)")
        
        # 子文件夹修改时间追踪表（用于快速判断父文件夹是否变化）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS child_modifications (
                parent_path TEXT NOT NULL,
                child_name TEXT NOT NULL,
                child_mtime REAL NOT NULL,
                child_size INTEGER DEFAULT 0,
                updated_at REAL DEFAULT (unixepoch()),
                
                PRIMARY KEY (parent_path, child_name),
                FOREIGN KEY (parent_path) REFERENCES file_tree(path) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_child_parent ON child_modifications(parent_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_child_mtime ON child_modifications(child_mtime)")
        
        conn.commit()
    
    # ==================== 基础CRUD操作 ====================
    
    def add_node(self, node: FileNode) -> bool:
        """添加或更新节点"""
        try:
            conn = self._get_conn()
            conn.execute("""
                INSERT OR REPLACE INTO file_tree 
                (path, parent_path, name, depth, is_dir, size, mtime, 
                 file_count, folder_count, content_hash, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                node.path, node.parent_path, node.name, node.depth,
                node.is_dir, node.size, node.mtime,
                node.file_count, node.folder_count, node.content_hash,
                time.time()
            ))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"添加节点失败 {node.path}: {e}")
            return False
    
    def add_nodes_batch(self, nodes: List[FileNode]) -> int:
        """批量添加节点（高效）"""
        if not nodes:
            return 0
        
        try:
            conn = self._get_conn()
            current_time = time.time()
            
            data = [
                (n.path, n.parent_path, n.name, n.depth, n.is_dir,
                 n.size, n.mtime, n.file_count, n.folder_count,
                 n.content_hash, current_time)
                for n in nodes
            ]
            
            conn.executemany("""
                INSERT OR REPLACE INTO file_tree 
                (path, parent_path, name, depth, is_dir, size, mtime,
                 file_count, folder_count, content_hash, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            conn.commit()
            return len(nodes)
        except sqlite3.Error as e:
            print(f"批量添加节点失败: {e}")
            return 0
    
    def get_node(self, path: str) -> Optional[FileNode]:
        """获取节点信息"""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM file_tree WHERE path = ?", (path,)
        )
        row = cursor.fetchone()
        
        if row:
            return FileNode(
                path=row['path'],
                name=row['name'],
                parent_path=row['parent_path'],
                depth=row['depth'],
                is_dir=bool(row['is_dir']),
                size=row['size'],
                mtime=row['mtime'],
                file_count=row['file_count'],
                folder_count=row['folder_count'],
                content_hash=row['content_hash'],
                updated_at=row['updated_at']
            )
        return None
    
    def delete_node(self, path: str) -> bool:
        """删除节点（级联删除子节点）"""
        try:
            conn = self._get_conn()
            conn.execute("DELETE FROM file_tree WHERE path = ?", (path,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"删除节点失败 {path}: {e}")
            return False
    
    # ==================== 树形查询操作 ====================
    
    def get_children(self, parent_path: str, include_files: bool = True, 
                     include_dirs: bool = True) -> List[FileNode]:
        """获取直接子节点"""
        conn = self._get_conn()
        
        conditions = ["parent_path = ?"]
        params = [parent_path]
        
        if include_files and not include_dirs:
            conditions.append("is_dir = 0")
        elif include_dirs and not include_files:
            conditions.append("is_dir = 1")
        
        sql = f"""
            SELECT * FROM file_tree 
            WHERE {' AND '.join(conditions)}
            ORDER BY is_dir DESC, name
        """
        
        cursor = conn.execute(sql, params)
        return [self._row_to_node(row) for row in cursor.fetchall()]
    
    def get_descendants(self, ancestor_path: str, max_depth: int = -1) -> List[FileNode]:
        """
        获取所有后代节点（利用路径前缀）
        
        Args:
            ancestor_path: 祖先路径
            max_depth: 最大深度（-1表示无限制）
        """
        conn = self._get_conn()
        
        # 确保路径以/结尾，避免前缀匹配问题
        prefix = ancestor_path.rstrip(os.sep) + os.sep
        
        if max_depth > 0:
            # 获取祖先深度
            cursor = conn.execute(
                "SELECT depth FROM file_tree WHERE path = ?", (ancestor_path,)
            )
            row = cursor.fetchone()
            ancestor_depth = row['depth'] if row else 0
            max_allowed_depth = ancestor_depth + max_depth
            
            sql = """
                SELECT * FROM file_tree 
                WHERE path LIKE ? AND depth <= ?
                ORDER BY depth, name
            """
            params = (prefix + '%', max_allowed_depth)
        else:
            sql = """
                SELECT * FROM file_tree 
                WHERE path LIKE ?
                ORDER BY depth, name
            """
            params = (prefix + '%',)
        
        cursor = conn.execute(sql, params)
        return [self._row_to_node(row) for row in cursor.fetchall()]
    
    def get_subtree(self, root_path: str, max_depth: int = -1) -> Optional[Dict]:
        """
        获取子树结构（嵌套字典格式）
        
        Returns:
            {
                'node': FileNode,
                'children': [
                    {'node': FileNode, 'children': [...]},
                    ...
                ]
            }
        """
        root_node = self.get_node(root_path)
        if not root_node:
            return None
        
        if not root_node.is_dir or max_depth == 0:
            return {'node': root_node, 'children': []}
        
        result = {'node': root_node, 'children': []}
        
        # 获取所有后代
        descendants = self.get_descendants(root_path, max_depth)
        
        # 构建树结构
        path_to_children: Dict[str, List[Dict]] = {root_path: result['children']}
        
        for node in descendants:
            node_dict = {'node': node, 'children': []}
            path_to_children[node.path] = node_dict['children']
            
            # 找到父节点并添加
            parent_children = path_to_children.get(node.parent_path)
            if parent_children is not None:
                parent_children.append(node_dict)
        
        return result
    
    def get_ancestors(self, path: str) -> List[FileNode]:
        """获取所有祖先节点（从根到父）"""
        ancestors = []
        current = self.get_node(path)
        
        while current and current.parent_path:
            parent = self.get_node(current.parent_path)
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break
        
        return list(reversed(ancestors))
    
    # ==================== 文件夹大小缓存操作 ====================
    
    def set_folder_size(self, path: str, size: int, file_count: int = 0,
                       folder_count: int = 0, mtime: float = 0,
                       content_hash: Optional[str] = None,
                       scan_duration_ms: int = 0):
        """设置文件夹大小缓存"""
        conn = self._get_conn()
        conn.execute("""
            INSERT OR REPLACE INTO folder_size_cache
            (path, size, file_count, folder_count, mtime, content_hash,
             last_scan_time, scan_duration_ms, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (path, size, file_count, folder_count, mtime, content_hash,
              time.time(), scan_duration_ms, time.time()))
        conn.commit()
    
    def get_folder_size(self, path: str) -> Optional[Dict]:
        """获取文件夹大小缓存"""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM folder_size_cache WHERE path = ?", (path,)
        )
        row = cursor.fetchone()
        
        if row:
            return {
                'path': row['path'],
                'size': row['size'],
                'file_count': row['file_count'],
                'folder_count': row['folder_count'],
                'mtime': row['mtime'],
                'content_hash': row['content_hash'],
                'last_scan_time': row['last_scan_time'],
                'scan_duration_ms': row['scan_duration_ms'],
                'updated_at': row['updated_at']
            }
        return None
    
    def is_folder_cache_valid(self, path: str, current_mtime: float,
                              current_hash: Optional[str] = None) -> bool:
        """
        检查文件夹大小缓存是否有效
        
        Args:
            path: 文件夹路径
            current_mtime: 当前修改时间
            current_hash: 当前内容哈希（可选，更精确的检查）
        
        Returns:
            True if cache is valid
        """
        cached = self.get_folder_size(path)
        if not cached:
            return False
        
        # 检查修改时间
        if cached['mtime'] != current_mtime:
            return False
        
        # 如果提供了哈希，也检查哈希
        if current_hash is not None and cached['content_hash'] != current_hash:
            return False
        
        return True
    
    # ==================== 子文件夹修改时间追踪 ====================
    
    def update_child_modifications(self, parent_path: str, 
                                   children_info: List[Tuple[str, float, int]]):
        """
        更新子文件夹修改时间信息
        
        Args:
            parent_path: 父文件夹路径
            children_info: [(child_name, child_mtime, child_size), ...]
        """
        if not children_info:
            return
        
        conn = self._get_conn()
        current_time = time.time()
        
        data = [
            (parent_path, name, mtime, size, current_time)
            for name, mtime, size in children_info
        ]
        
        conn.executemany("""
            INSERT OR REPLACE INTO child_modifications
            (parent_path, child_name, child_mtime, child_size, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, data)
        conn.commit()
    
    def get_child_modifications(self, parent_path: str) -> Dict[str, Dict]:
        """获取子文件夹修改时间信息"""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT child_name, child_mtime, child_size, updated_at
            FROM child_modifications
            WHERE parent_path = ?
        """, (parent_path,))
        
        return {
            row['child_name']: {
                'mtime': row['child_mtime'],
                'size': row['child_size'],
                'updated_at': row['updated_at']
            }
            for row in cursor.fetchall()
        }
    
    def has_children_changed(self, parent_path: str, 
                            current_children: List[Tuple[str, float]]) -> bool:
        """
        快速检查子文件夹是否发生变化
        
        Args:
            parent_path: 父文件夹路径
            current_children: [(child_name, child_mtime), ...]
        
        Returns:
            True if any child has changed
        """
        cached = self.get_child_modifications(parent_path)
        
        # 检查数量是否变化
        if len(cached) != len(current_children):
            return True
        
        # 检查每个子文件夹
        for name, mtime in current_children:
            if name not in cached:
                return True  # 新增子文件夹
            if cached[name]['mtime'] != mtime:
                return True  # 修改时间变化
        
        return False
    
    # ==================== 统计和搜索 ====================
    
    def search_by_name(self, name_pattern: str, limit: int = 100,
                       is_dir: Optional[bool] = None) -> List[FileNode]:
        """按名称搜索"""
        conn = self._get_conn()
        
        sql = "SELECT * FROM file_tree WHERE name LIKE ?"
        params = [f'%{name_pattern}%']
        
        if is_dir is not None:
            sql += " AND is_dir = ?"
            params.append(1 if is_dir else 0)
        
        sql += " ORDER BY is_dir DESC, name LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(sql, params)
        return [self._row_to_node(row) for row in cursor.fetchall()]
    
    def get_tree_stats(self, root_path: str) -> Dict:
        """获取树的统计信息"""
        prefix = root_path.rstrip(os.sep) + os.sep
        conn = self._get_conn()
        
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_nodes,
                SUM(CASE WHEN is_dir = 0 THEN 1 ELSE 0 END) as file_count,
                SUM(CASE WHEN is_dir = 1 THEN 1 ELSE 0 END) as folder_count,
                SUM(CASE WHEN is_dir = 0 THEN size ELSE 0 END) as total_file_size
            FROM file_tree 
            WHERE path LIKE ? OR path = ?
        """, (prefix + '%', root_path))
        
        row = cursor.fetchone()
        
        # 获取预计算的文件夹大小
        cursor = conn.execute("""
            SELECT SUM(size) as total_size
            FROM folder_size_cache
            WHERE path LIKE ? OR path = ?
        """, (prefix + '%', root_path))
        
        size_row = cursor.fetchone()
        
        return {
            'total_nodes': row['total_nodes'] or 0,
            'file_count': row['file_count'] or 0,
            'folder_count': row['folder_count'] or 0,
            'total_file_size': row['total_file_size'] or 0,
            'cached_folder_size': size_row['total_size'] or 0
        }
    
    def get_stale_cache(self, max_age_seconds: float = 86400) -> List[str]:
        """获取过期的缓存项"""
        cutoff_time = time.time() - max_age_seconds
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT path FROM folder_size_cache WHERE updated_at < ?",
            (cutoff_time,)
        )
        return [row['path'] for row in cursor.fetchall()]
    
    def cleanup_stale_cache(self, max_age_seconds: float = 86400) -> int:
        """清理过期的缓存"""
        cutoff_time = time.time() - max_age_seconds
        conn = self._get_conn()
        cursor = conn.execute(
            "DELETE FROM folder_size_cache WHERE updated_at < ?",
            (cutoff_time,)
        )
        conn.commit()
        return cursor.rowcount
    
    # ==================== 辅助方法 ====================
    
    def _row_to_node(self, row: sqlite3.Row) -> FileNode:
        """将数据库行转换为FileNode"""
        return FileNode(
            path=row['path'],
            name=row['name'],
            parent_path=row['parent_path'],
            depth=row['depth'],
            is_dir=bool(row['is_dir']),
            size=row['size'],
            mtime=row['mtime'],
            file_count=row['file_count'],
            folder_count=row['folder_count'],
            content_hash=row['content_hash'],
            updated_at=row['updated_at']
        )
    
    @staticmethod
    def compute_content_hash(children_info: List[Tuple[str, float, int]]) -> str:
        """
        计算内容哈希（用于检测文件夹内容变化）
        
        Args:
            children_info: [(name, mtime, size), ...]
        
        Returns:
            哈希字符串
        """
        # 按名称排序确保一致性
        sorted_info = sorted(children_info, key=lambda x: x[0])
        content = '|'.join(f"{n}:{m}:{s}" for n, m, s in sorted_info)
        return hashlib.blake2b(content.encode(), digest_size=16).hexdigest()
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
