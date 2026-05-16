"""
文件树管理器 - 业务逻辑层

设计思想：
1. 分层架构：Database(存储) -> Manager(业务) -> UI(展示)
2. 懒加载：不一次性加载整棵树，按需查询
3. 缓存策略：内存缓存 + 数据库持久化
4. 变化检测：多种策略检测文件夹变化
5. 批量优化：减少数据库操作次数
"""

import os
import time
import threading
from pathlib import Path
from typing import Optional, List, Dict, Callable, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from dbload_manager.file_tree_database import FileTreeDatabase, FileNode


logger = logging.getLogger(__name__)


class CacheValidity(Enum):
    """缓存有效性状态"""
    VALID = "valid"           # 缓存有效
    MTIME_CHANGED = "mtime"   # 修改时间变化
    CONTENT_CHANGED = "content"  # 内容变化
    NOT_CACHED = "none"       # 未缓存
    STALE = "stale"           # 缓存过期


@dataclass
class FolderInfo:
    """文件夹信息（用于UI展示）"""
    path: str
    name: str
    size: int
    formatted_size: str
    file_count: int
    folder_count: int
    mtime: float
    is_accessible: bool = True
    cache_status: CacheValidity = CacheValidity.NOT_CACHED


class FileTreeManager:
    """
    文件树管理器
    
    职责：
    1. 管理文件树数据库的生命周期
    2. 提供文件夹大小缓存的获取和更新
    3. 实现变化检测策略
    4. 内存缓存热点数据
    5. 批量操作优化
    
    使用示例：
        with FileTreeManager() as manager:
            # 获取文件夹大小（自动使用缓存）
            info = manager.get_folder_info("/path/to/folder")
            
            # 扫描完成后更新缓存
            manager.update_folder_size("/path/to/folder", total_size, 
                                       file_count, folder_count)
    """
    
    def __init__(self, db_path: str = "userdata/db/file_tree.db"):
        self.db = FileTreeDatabase(db_path)
        
        # 内存缓存：热点文件夹大小
        self._memory_cache: Dict[str, Dict] = {}
        self._memory_cache_lock = threading.RLock()
        self._memory_cache_max_size = 1000  # 最多缓存1000个文件夹
        
        # 访问计数（用于LRU淘汰）
        self._access_count: Dict[str, int] = {}
        
        # 变化检测策略
        self._check_content_hash = False  # 是否检查内容哈希
        self._cache_max_age = 360 * 24 * 3600  # 缓存最大存活360天（提高过期时间）
        
        # 统计信息
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'db_queries': 0,
            'db_updates': 0
        }
    
    # ==================== 核心API：文件夹大小获取 ====================
    
    def get_folder_info(self, folder_path: str, 
                       force_rescan: bool = False) -> FolderInfo:
        """
        获取文件夹信息（智能使用缓存）
        
        这是主要API，UI层直接调用此方法获取文件夹大小
        
        Args:
            folder_path: 文件夹路径
            force_rescan: 是否强制重新扫描
        
        Returns:
            FolderInfo对象
        """
        folder_path = os.path.normpath(folder_path)
        
        # 1. 检查内存缓存
        if not force_rescan:
            mem_cached = self._get_from_memory_cache(folder_path)
            if mem_cached:
                # logger.info(f"[缓存命中-内存] {folder_path}")
                self._stats['cache_hits'] += 1
                return self._create_folder_info(mem_cached, CacheValidity.VALID)
        
        # 2. 检查数据库缓存
        if not force_rescan:
            db_cached = self.db.get_folder_size(folder_path)
            if db_cached:
                self._stats['db_queries'] += 1
                
                # 验证缓存有效性
                validity = self._check_cache_validity(folder_path, db_cached)
                
                if validity == CacheValidity.VALID:
                    # 更新内存缓存
                    self._add_to_memory_cache(folder_path, db_cached)
                    # logger.info(f"[缓存命中-数据库] {folder_path}")
                    self._stats['cache_hits'] += 1
                    return self._create_folder_info(db_cached, validity)
                else:
                    # 缓存失效
                    self._stats['cache_misses'] += 1
                    logger.debug(f"缓存失效 [{validity.value}]: {folder_path}")
        
        # 3. 无有效缓存
        self._stats['cache_misses'] += 1
        logger.debug(f"[缓存未命中] {folder_path}，需要重新计算")
        return FolderInfo(
            path=folder_path,
            name=os.path.basename(folder_path),
            size=0,
            formatted_size="计算中...",
            file_count=0,
            folder_count=0,
            mtime=0,
            is_accessible=True,
            cache_status=CacheValidity.NOT_CACHED
        )
    
    def update_folder_size(self, folder_path: str, size: int,
                          file_count: int = 0, folder_count: int = 0,
                          scan_duration_ms: int = 0) -> bool:
        """
        更新文件夹大小缓存（扫描完成后调用）
        
        Args:
            folder_path: 文件夹路径
            size: 总大小（字节）
            file_count: 文件数量
            folder_count: 子文件夹数量
            scan_duration_ms: 扫描耗时
        
        Returns:
            是否成功
        """
        folder_path = os.path.normpath(folder_path)
        
        try:
            # 获取当前修改时间
            current_mtime = os.path.getmtime(folder_path)
            
            # 计算内容哈希（可选）
            content_hash = None
            if self._check_content_hash:
                content_hash = self._compute_folder_hash(folder_path)
            
            # 更新数据库
            self.db.set_folder_size(
                path=folder_path,
                size=size,
                file_count=file_count,
                folder_count=folder_count,
                mtime=current_mtime,
                content_hash=content_hash,
                scan_duration_ms=scan_duration_ms
            )
            self._stats['db_updates'] += 1
            
            # 更新内存缓存
            cached_data = {
                'path': folder_path,
                'size': size,
                'file_count': file_count,
                'folder_count': folder_count,
                'mtime': current_mtime,
                'content_hash': content_hash,
                'updated_at': time.time()
            }
            self._add_to_memory_cache(folder_path, cached_data)
            
            # 更新子文件夹修改时间信息（用于父文件夹快速检测）
            self._update_child_modifications(folder_path)

            # 级联使父文件夹缓存失效
            # 当子文件夹大小更新时，所有祖先文件夹的缓存都应该失效
            self._invalidate_parent_caches(folder_path)

            logger.debug(f"更新缓存: {folder_path} = {size} bytes")
            return True
            
        except OSError as e:
            logger.error(f"更新文件夹大小失败 {folder_path}: {e}")
            return False
    
    def mark_folder_inaccessible(self, folder_path: str):
        """标记文件夹为不可访问"""
        folder_path = os.path.normpath(folder_path)
        # 从缓存中移除
        with self._memory_cache_lock:
            self._memory_cache.pop(folder_path, None)
            self._access_count.pop(folder_path, None)
    
    # ==================== 变化检测策略 ====================
    
    def _check_cache_validity(self, folder_path: str,
                              cached_data: Dict) -> CacheValidity:
        """
        检查缓存有效性

        策略优先级（调整后的顺序）：
        1. 检查缓存是否过期
        2. 检查子文件夹修改时间（优先检查，因为父文件夹mtime不会随子文件夹变化）
        3. 检查修改时间
        4. 检查内容哈希（如果启用）
        """
        # 1. 检查过期时间
        cache_age = time.time() - cached_data.get('updated_at', 0)
        if cache_age > self._cache_max_age:
            # logger.warning(f"[缓存失效原因-过期] {folder_path}, 年龄: {cache_age/86400:.1f}天")
            return CacheValidity.STALE

        # 2. 快速子文件夹检查（移到前面，优先执行）
        # 原因：在Windows等系统中，子文件夹内容变化不会更新父文件夹的mtime
        if self._has_children_changed_quick(folder_path):
            # logger.warning(f"[缓存失效原因-子文件夹变化] {folder_path}")
            return CacheValidity.CONTENT_CHANGED

        try:
            current_mtime = os.path.getmtime(folder_path)
        except OSError:
            # logger.warning(f"[缓存失效原因-文件夹不存在] {folder_path}")
            return CacheValidity.NOT_CACHED  # 文件夹已不存在

        # 3. 检查修改时间（自身mtime变化）
        cached_mtime = cached_data.get('mtime', 0)
        mtime_diff = abs(cached_mtime - current_mtime)
        if mtime_diff > 0.001:  # 允许1毫秒误差
            # logger.warning(f"[缓存失效原因-mtime变化] {folder_path}, 缓存: {cached_mtime}, 当前: {current_mtime}, 差值: {mtime_diff:.6f}秒")
            return CacheValidity.MTIME_CHANGED
        elif cached_mtime != current_mtime:
            logger.debug(f"[mtime微小变化忽略] {folder_path}, 差值: {mtime_diff:.6f}秒")

        # 4. 检查内容哈希（如果启用且存在）
        if self._check_content_hash and cached_data.get('content_hash'):
            current_hash = self._compute_folder_hash(folder_path)
            if current_hash != cached_data['content_hash']:
                # logger.warning(f"[缓存失效原因-哈希变化] {folder_path}")
                return CacheValidity.CONTENT_CHANGED

        # logger.info(f"[缓存有效] {folder_path}")
        return CacheValidity.VALID
    
    def _has_children_changed_quick(self, folder_path: str) -> bool:
        """
        快速检查子文件夹是否变化（不遍历内容）

        利用预先存储的子文件夹修改时间信息
        """
        try:
            # 获取当前子文件夹列表（包含大小信息）
            current_children = []
            access_errors = 0
            with os.scandir(folder_path) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        try:
                            stat = entry.stat(follow_symlinks=False)
                            # 同时传递修改时间和大小，用于更精确的变化检测
                            current_children.append((entry.name, stat.st_mtime, stat.st_size))
                        except (OSError, PermissionError):
                            access_errors += 1
                            pass

            # 如果存在访问错误，说明无法完整获取子文件夹列表
            # 此时跳过子文件夹变化检查，依赖 mtime 检查来判断缓存有效性
            if access_errors > 0:
                logger.debug(f"[子文件夹检查-部分无法访问] {folder_path}: 成功={len(current_children)}, 失败={access_errors}, 跳过子文件夹变化检查")
                return False  # 跳过子文件夹检查，不因此失效缓存

            # 使用数据库快速比较
            has_changed = self.db.has_children_changed(folder_path, current_children)
            # if has_changed:
            #     logger.warning(f"[子文件夹变化检查] {folder_path}: 当前子文件夹数={len(current_children)}")
            return has_changed

        except (OSError, PermissionError) as e:
            # logger.warning(f"[子文件夹变化检查-无法访问] {folder_path}: {e}")
            return False  # 完全无法访问时，不因此失效缓存（依赖 mtime 检查）
    
    def _compute_folder_hash(self, folder_path: str) -> Optional[str]:
        """计算文件夹内容哈希"""
        try:
            children_info = []
            with os.scandir(folder_path) as it:
                for entry in it:
                    try:
                        stat = entry.stat(follow_symlinks=False)
                        children_info.append((entry.name, stat.st_mtime, stat.st_size))
                    except (OSError, PermissionError):
                        pass

            return FileTreeDatabase.compute_content_hash(children_info)

        except (OSError, PermissionError):
            return None

    # ==================== 智能树结构大小计算 ====================

    def calculate_folder_size_smart(self, folder_path: str) -> Dict:
        """
        智能计算文件夹大小 - 利用缓存避免重复计算

        算法：
        1. 检查当前文件夹缓存是否有效
        2. 如果有效，直接返回缓存值
        3. 如果无效，检查哪些子文件夹需要重新计算
        4. 只计算需要更新的子文件夹，累加有效缓存的子文件夹大小

        Args:
            folder_path: 文件夹路径

        Returns:
            {
                'size': 总大小（字节）,
                'file_count': 文件数,
                'folder_count': 子文件夹数,
                'cached_used': 使用的缓存数,
                'recalculated': 重新计算的文件夹数,
                'is_fully_cached': 是否完全来自缓存
            }
        """
        folder_path = os.path.normpath(folder_path)

        # 1. 首先检查当前文件夹缓存
        folder_info = self.get_folder_info(folder_path)
        if folder_info.cache_status == CacheValidity.VALID:
            logger.debug(f"使用缓存: {folder_path}")
            return {
                'size': folder_info.size,
                'file_count': folder_info.file_count,
                'folder_count': folder_info.folder_count,
                'cached_used': 1,
                'recalculated': 0,
                'is_fully_cached': True
            }

        # 2. 缓存无效，需要重新计算
        return self._calculate_size_recursive(folder_path)

    def _calculate_size_recursive(self, folder_path: str) -> Dict:
        """
        递归计算文件夹大小，智能使用缓存

        Returns:
            大小信息字典
        """
        folder_path = os.path.normpath(folder_path)
        total_size = 0
        total_files = 0
        total_folders = 0
        cached_used = 0
        recalculated = 0

        try:
            # 检查当前文件夹缓存
            folder_info = self.get_folder_info(folder_path)

            if folder_info.cache_status == CacheValidity.VALID:
                # 使用缓存
                logger.debug(f"递归中使用缓存: {folder_path}")
                return {
                    'size': folder_info.size,
                    'file_count': folder_info.file_count,
                    'folder_count': folder_info.folder_count,
                    'cached_used': 1,
                    'recalculated': 0,
                    'is_fully_cached': True
                }

            # 需要计算当前文件夹
            recalculated += 1

            # 遍历当前文件夹内容
            with os.scandir(folder_path) as it:
                for entry in it:
                    if not self._is_running:
                        break

                    try:
                        if entry.is_dir(follow_symlinks=False):
                            # 递归计算子文件夹
                            sub_result = self._calculate_size_recursive(entry.path)

                            total_size += sub_result['size']
                            total_files += sub_result['file_count']
                            total_folders += 1 + sub_result['folder_count']
                            cached_used += sub_result['cached_used']
                            recalculated += sub_result['recalculated']

                        else:
                            # 文件直接累加
                            try:
                                total_size += max(entry.stat(follow_symlinks=False).st_size, 0)
                                total_files += 1
                            except (OSError, PermissionError):
                                pass

                    except (OSError, PermissionError) as e:
                        logger.debug(f"无法访问 {entry.path}: {e}")
                        continue

            # 更新当前文件夹缓存
            self.update_folder_size(
                folder_path=folder_path,
                size=total_size,
                file_count=total_files,
                folder_count=total_folders
            )

            return {
                'size': total_size,
                'file_count': total_files,
                'folder_count': total_folders,
                'cached_used': cached_used,
                'recalculated': recalculated,
                'is_fully_cached': False
            }

        except (OSError, PermissionError) as e:
            logger.error(f"计算文件夹大小失败 {folder_path}: {e}")
            return {
                'size': 0,
                'file_count': 0,
                'folder_count': 0,
                'cached_used': 0,
                'recalculated': 0,
                'is_fully_cached': False
            }

    def update_folder_tree_sizes_smart(self, root_path: str) -> Dict:
        """
        智能更新整个文件夹树的大小 - 只计算需要更新的部分

        Args:
            root_path: 根文件夹路径

        Returns:
            {
                'total_folders': 总文件夹数,
                'cached_used': 使用的缓存数,
                'recalculated': 重新计算的文件夹数,
                'cache_hit_rate': 缓存命中率
            }
        """
        root_path = os.path.normpath(root_path)

        logger.info(f"开始智能更新树结构大小: {root_path}")

        result = self._calculate_size_recursive(root_path)

        total_folders = result['cached_used'] + result['recalculated']
        cache_hit_rate = (result['cached_used'] / total_folders * 100) if total_folders > 0 else 0

        stats = {
            'total_folders': total_folders,
            'cached_used': result['cached_used'],
            'recalculated': result['recalculated'],
            'cache_hit_rate': cache_hit_rate
        }

        logger.info(f"智能更新完成: {root_path}, 缓存命中率: {cache_hit_rate:.1f}% "
                   f"({result['cached_used']}/{total_folders})")

        return stats

    def get_subtree_size_info(self, root_path: str) -> Dict[str, Dict]:
        """
        获取子树中所有文件夹的大小信息

        利用已缓存的数据，避免重复计算

        Args:
            root_path: 根文件夹路径

        Returns:
            {path: {'size': ..., 'formatted_size': ..., 'is_cached': ...}, ...}
        """
        root_path = os.path.normpath(root_path)
        result = {}

        try:
            for current_path, dirs, files in os.walk(root_path, followlinks=False):
                folder_info = self.get_folder_info(current_path)

                result[current_path] = {
                    'size': folder_info.size,
                    'formatted_size': folder_info.formatted_size,
                    'file_count': folder_info.file_count,
                    'folder_count': folder_info.folder_count,
                    'is_cached': folder_info.cache_status == CacheValidity.VALID,
                    'cache_status': folder_info.cache_status.value
                }

        except Exception as e:
            logger.error(f"获取子树大小信息失败 {root_path}: {e}")

        return result

    # 用于控制递归计算的运行状态
    _is_running = True

    def stop_calculation(self):
        """停止正在进行的计算"""
        self._is_running = False
    
    def _update_child_modifications(self, parent_path: str):
        """更新子文件夹修改时间信息"""
        try:
            children_info = []
            with os.scandir(parent_path) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        try:
                            stat = entry.stat(follow_symlinks=False)
                            children_info.append((entry.name, stat.st_mtime, stat.st_size))
                        except (OSError, PermissionError):
                            pass

            self.db.update_child_modifications(parent_path, children_info)

        except (OSError, PermissionError):
            pass

    def _invalidate_parent_caches(self, folder_path: str):
        """
        级联使父文件夹缓存失效

        当子文件夹大小更新时，所有祖先文件夹的缓存都应该失效，
        因为它们的大小包含了子文件夹的大小。
        """
        current = folder_path
        while True:
            parent = os.path.dirname(current)
            if not parent or parent == current:
                break

            # 从内存缓存中移除父文件夹
            with self._memory_cache_lock:
                if parent in self._memory_cache:
                    self._memory_cache.pop(parent, None)
                    self._access_count.pop(parent, None)
                    logger.debug(f"级联失效父文件夹缓存: {parent}")

            # 更新父文件夹的子文件夹修改时间记录
            # 这确保父文件夹的 child_modifications 表中有当前文件夹的记录
            self._update_parent_child_modifications(parent, current)

            current = parent

    def _update_parent_child_modifications(self, parent_path: str, child_path: str):
        """
        更新父文件夹中特定子文件夹的修改时间记录

        当子文件夹更新时，需要确保父文件夹的 child_modifications 表中有该子文件夹的最新记录，
        避免下次检查父文件夹缓存时被误判为"子文件夹变化"。
        """
        try:
            child_name = os.path.basename(child_path)
            stat = os.stat(child_path)
            # 更新父文件夹的子文件夹记录
            self.db.update_child_modifications(parent_path, [(child_name, stat.st_mtime, stat.st_size)])
            logger.debug(f"更新父文件夹子文件夹记录: {parent_path}/{child_name}")
        except (OSError, PermissionError) as e:
            logger.debug(f"更新父文件夹子文件夹记录失败 {parent_path}/{child_path}: {e}")
    
    # ==================== 内存缓存管理 ====================
    
    def _get_from_memory_cache(self, folder_path: str) -> Optional[Dict]:
        """从内存缓存获取"""
        with self._memory_cache_lock:
            if folder_path in self._memory_cache:
                # 更新访问计数
                self._access_count[folder_path] = self._access_count.get(folder_path, 0) + 1
                return self._memory_cache[folder_path]
        return None
    
    def _add_to_memory_cache(self, folder_path: str, data: Dict):
        """添加到内存缓存（带LRU淘汰）"""
        with self._memory_cache_lock:
            # 检查是否需要淘汰
            if len(self._memory_cache) >= self._memory_cache_max_size:
                # LRU淘汰：移除访问次数最少的
                if self._access_count:
                    min_key = min(self._access_count, key=self._access_count.get)
                    self._memory_cache.pop(min_key, None)
                    self._access_count.pop(min_key, None)
            
            self._memory_cache[folder_path] = data
            self._access_count[folder_path] = self._access_count.get(folder_path, 0) + 1
    
    def clear_memory_cache(self):
        """清空内存缓存"""
        with self._memory_cache_lock:
            self._memory_cache.clear()
            self._access_count.clear()
    
    # ==================== 批量操作 ====================
    
    def preload_folder_sizes(self, folder_paths: List[str]) -> Dict[str, FolderInfo]:
        """
        预加载多个文件夹大小（用于批量显示）
        
        Args:
            folder_paths: 文件夹路径列表
        
        Returns:
            {path: FolderInfo, ...}
        """
        results = {}
        
        for path in folder_paths:
            path = os.path.normpath(path)
            info = self.get_folder_info(path)
            results[path] = info
        
        return results
    
    def invalidate_cache(self, folder_path: str, include_children: bool = False):
        """
        使缓存失效
        
        Args:
            folder_path: 文件夹路径
            include_children: 是否包含子文件夹
        """
        folder_path = os.path.normpath(folder_path)
        
        # 从内存缓存移除
        with self._memory_cache_lock:
            self._memory_cache.pop(folder_path, None)
            self._access_count.pop(folder_path, None)
        
        if include_children:
            # 使所有子文件夹缓存失效
            prefix = folder_path.rstrip(os.sep) + os.sep
            with self._memory_cache_lock:
                keys_to_remove = [
                    k for k in self._memory_cache.keys()
                    if k.startswith(prefix)
                ]
                for k in keys_to_remove:
                    self._memory_cache.pop(k, None)
                    self._access_count.pop(k, None)
    
    def invalidate_all_cache(self):
        """使所有缓存失效"""
        self.clear_memory_cache()
        # 可选：清空数据库缓存
        # self.db.cleanup_all_cache()
    
    # ==================== 辅助方法 ====================
    
    def _create_folder_info(self, cached_data: Dict, 
                           validity: CacheValidity) -> FolderInfo:
        """创建FolderInfo对象"""
        from utils.size_utils import format_size
        
        size = cached_data.get('size', 0)
        
        return FolderInfo(
            path=cached_data.get('path', ''),
            name=os.path.basename(cached_data.get('path', '')),
            size=size,
            formatted_size=format_size(size) if size > 0 else "0B",
            file_count=cached_data.get('file_count', 0),
            folder_count=cached_data.get('folder_count', 0),
            mtime=cached_data.get('mtime', 0),
            is_accessible=True,
            cache_status=validity
        )
    
    # ==================== 配置和统计 ====================
    
    def set_check_content_hash(self, enabled: bool):
        """设置是否检查内容哈希"""
        self._check_content_hash = enabled
    
    def set_cache_max_age(self, seconds: float):
        """设置缓存最大存活时间"""
        self._cache_max_age = seconds
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self._stats,
            'memory_cache_size': len(self._memory_cache),
            'memory_cache_max': self._memory_cache_max_size
        }
    
    def cleanup_stale_cache(self, max_age_days: int = 7) -> int:
        """清理过期缓存"""
        max_age_seconds = max_age_days * 24 * 3600
        return self.db.cleanup_stale_cache(max_age_seconds)

    # ==================== 树结构大小管理 ====================

    def update_folder_tree_sizes(self, root_path: str) -> Dict[str, int]:
        """
        递归更新整个文件夹树的大小

        扫描所有子文件夹并缓存它们的大小，返回每个路径的大小

        Args:
            root_path: 根文件夹路径

        Returns:
            {path: size, ...} 所有子文件夹的大小映射
        """
        root_path = os.path.normpath(root_path)
        sizes = {}

        try:
            # 使用 os.walk 递归遍历
            for current_path, dirs, files in os.walk(root_path, followlinks=False):
                if not os.path.exists(current_path):
                    continue

                # 计算当前文件夹大小
                total_size = 0
                file_count = len(files)
                folder_count = len(dirs)

                # 累加文件大小
                for file in files:
                    try:
                        file_path = os.path.join(current_path, file)
                        total_size += max(os.path.getsize(file_path), 0)
                    except (OSError, PermissionError):
                        pass

                # 存储当前文件夹大小
                self.update_folder_size(
                    folder_path=current_path,
                    size=total_size,
                    file_count=file_count,
                    folder_count=folder_count
                )
                sizes[current_path] = total_size

            logger.info(f"树结构大小更新完成: {root_path}, 共 {len(sizes)} 个文件夹")
            return sizes

        except Exception as e:
            logger.error(f"更新树结构大小失败 {root_path}: {e}")
            return sizes

    def get_child_folders_info(self, parent_path: str) -> List[FolderInfo]:
        """
        获取子文件夹信息列表（按需加载）

        Args:
            parent_path: 父文件夹路径

        Returns:
            FolderInfo 列表
        """
        parent_path = os.path.normpath(parent_path)
        results = []

        try:
            # 获取直接子文件夹
            with os.scandir(parent_path) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        folder_info = self.get_folder_info(entry.path)
                        results.append(folder_info)
        except (OSError, PermissionError) as e:
            logger.error(f"获取子文件夹信息失败 {parent_path}: {e}")

        return results

    def get_folder_tree_stats(self, root_path: str) -> Dict:
        """
        获取文件夹树的统计信息

        Args:
            root_path: 根文件夹路径

        Returns:
            {
                'total_size': 总大小,
                'total_files': 总文件数,
                'total_folders': 总文件夹数,
                'cached_count': 已缓存的文件夹数,
                'uncached_count': 未缓存的文件夹数
            }
        """
        root_path = os.path.normpath(root_path)
        stats = {
            'total_size': 0,
            'total_files': 0,
            'total_folders': 0,
            'cached_count': 0,
            'uncached_count': 0
        }

        try:
            for current_path, dirs, files in os.walk(root_path, followlinks=False):
                folder_info = self.get_folder_info(current_path)

                if folder_info.cache_status == CacheValidity.VALID:
                    stats['total_size'] += folder_info.size
                    stats['total_files'] += folder_info.file_count
                    stats['cached_count'] += 1
                else:
                    stats['uncached_count'] += 1
                    # 估算未缓存文件夹的大小
                    try:
                        for file in files:
                            file_path = os.path.join(current_path, file)
                            stats['total_size'] += max(os.path.getsize(file_path), 0)
                        stats['total_files'] += len(files)
                    except (OSError, PermissionError):
                        pass

                stats['total_folders'] += len(dirs)

        except Exception as e:
            logger.error(f"获取树统计信息失败 {root_path}: {e}")

        return stats

    def cascade_invalidate_cache(self, folder_path: str):
        """
        级联使缓存失效（子文件夹和父文件夹）

        当文件夹内容变化时，需要使该文件夹及其所有祖先的缓存失效

        Args:
            folder_path: 变化的文件夹路径
        """
        folder_path = os.path.normpath(folder_path)

        # 1. 使当前文件夹及其所有子文件夹缓存失效
        self.invalidate_cache(folder_path, include_children=True)

        # 2. 使所有祖先文件夹缓存失效
        try:
            current = folder_path
            while True:
                parent = os.path.dirname(current)
                if not parent or parent == current:
                    break

                # 使父文件夹缓存失效（不包含子文件夹，避免重复）
                self.invalidate_cache(parent, include_children=False)
                current = parent

            logger.debug(f"级联缓存失效完成: {folder_path}")
        except Exception as e:
            logger.error(f"级联缓存失效失败 {folder_path}: {e}")

    # ==================== 上下文管理器 ====================
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    def close(self):
        """关闭管理器"""
        self.db.close()
