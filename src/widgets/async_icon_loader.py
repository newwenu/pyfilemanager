"""
异步图标加载器

解决大目录图标加载卡顿问题：
- 后台线程加载图标
- 图标缓存
- 优先级队列（可见区域优先）
"""
from PySide6.QtCore import QThread, Signal, QObject, QMutex, QWaitCondition
from PySide6.QtGui import QIcon, QPixmap
from typing import Dict, List, Optional, Callable, Set
from collections import deque
import os


class IconLoadTask:
    """图标加载任务"""
    def __init__(self, file_path: str, callback: Callable[[str, QIcon], None], priority: int = 0):
        self.file_path = file_path
        self.callback = callback
        self.priority = priority
    
    def __lt__(self, other):
        # 优先级高的先执行（数字小的优先级高）
        return self.priority < other.priority


class AsyncIconLoaderThread(QThread):
    """异步图标加载线程"""
    
    icon_loaded = Signal(str, QIcon)  # file_path, icon
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks: deque = deque()
        self._mutex = QMutex()
        self._condition = QWaitCondition()
        self._is_running = True
        self._cache: Dict[str, QIcon] = {}
        self._cache_limit = 1000  # 缓存限制
    
    def add_task(self, file_path: str, priority: int = 0):
        """添加加载任务"""
        # 检查缓存
        if file_path in self._cache:
            # 从缓存直接返回
            self.icon_loaded.emit(file_path, self._cache[file_path])
            return
        
        self._mutex.lock()
        # 检查是否已在队列中
        for task in self._tasks:
            if task.file_path == file_path:
                # 更新优先级
                task.priority = min(task.priority, priority)
                self._mutex.unlock()
                return
        
        # 添加新任务
        task = IconLoadTask(
            file_path, 
            lambda path, icon: self.icon_loaded.emit(path, icon),
            priority
        )
        
        # 按优先级插入（高优先级在前）
        inserted = False
        for i, t in enumerate(self._tasks):
            if task.priority < t.priority:
                self._tasks.insert(i, task)
                inserted = True
                break
        if not inserted:
            self._tasks.append(task)
        
        self._condition.wakeOne()
        self._mutex.unlock()
    
    def add_tasks(self, file_paths: List[str], priority: int = 0):
        """批量添加任务"""
        for path in file_paths:
            self.add_task(path, priority)
    
    def clear_tasks(self):
        """清空任务队列"""
        self._mutex.lock()
        self._tasks.clear()
        self._mutex.unlock()
    
    def stop(self):
        """停止线程"""
        self._is_running = False
        self._mutex.lock()
        self._condition.wakeAll()
        self._mutex.unlock()
    
    def _load_icon(self, file_path: str) -> Optional[QIcon]:
        """加载单个图标"""
        try:
            from image_manager.icon_manager_factory import get_icon_manager
            from image_manager.ink_icon import get_shortcut_icon_pixmap
            
            icon_manager = get_icon_manager()
            
            # 特殊处理快捷方式
            if file_path.endswith('.lnk'):
                pixmap = get_shortcut_icon_pixmap(file_path, 32)
                if pixmap and not pixmap.isNull():
                    return QIcon(pixmap)
            
            # 普通文件
            ext = os.path.splitext(file_path)[1].lower()
            icon = icon_manager.get_icon(ext)
            if icon:
                return icon
            
            return None
        except Exception:
            return None
    
    def _add_to_cache(self, file_path: str, icon: QIcon):
        """添加图标到缓存"""
        # 如果缓存已满，移除最旧的
        if len(self._cache) >= self._cache_limit:
            # 简单策略：移除第一个
            if self._cache:
                oldest = next(iter(self._cache))
                del self._cache[oldest]
        
        self._cache[file_path] = icon
    
    def run(self):
        """线程主循环"""
        while self._is_running:
            self._mutex.lock()
            
            # 等待任务
            while self._is_running and not self._tasks:
                self._condition.wait(self._mutex)
            
            if not self._is_running:
                self._mutex.unlock()
                break
            
            # 获取任务
            task = self._tasks.popleft()
            self._mutex.unlock()
            
            # 加载图标
            icon = self._load_icon(task.file_path)
            if icon:
                # 添加到缓存
                self._add_to_cache(task.file_path, icon)
                # 回调
                task.callback(task.file_path, icon)


class AsyncIconLoader(QObject):
    """
    异步图标加载器
    
    管理图标的后台加载，支持：
    - 优先级队列（可见区域优先加载）
    - 图标缓存
    - 批量加载
    """
    
    icon_ready = Signal(str, QIcon)  # file_path, icon
    
    # 优先级定义
    PRIORITY_VISIBLE = 0      # 可见区域（最高优先级）
    PRIORITY_NEARBY = 10      # 附近区域
    PRIORITY_BACKGROUND = 100 # 后台加载
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建加载线程
        self._loader_thread = AsyncIconLoaderThread(self)
        self._loader_thread.icon_loaded.connect(self._on_icon_loaded)
        self._loader_thread.start()
        
        # 待处理的更新回调
        self._pending_updates: Dict[str, Callable[[QIcon], None]] = {}
    
    def load_icon(self, file_path: str, 
                  update_callback: Callable[[QIcon], None],
                  priority: int = PRIORITY_BACKGROUND):
        """
        异步加载图标
        
        Args:
            file_path: 文件路径
            update_callback: 图标加载完成后的回调函数
            priority: 加载优先级
        """
        # 保存回调
        self._pending_updates[file_path] = update_callback
        
        # 添加到加载队列
        self._loader_thread.add_task(file_path, priority)
    
    def load_icons_batch(self, file_paths: List[str],
                         update_callback: Callable[[str, QIcon], None],
                         priority: int = PRIORITY_BACKGROUND):
        """
        批量加载图标
        
        Args:
            file_paths: 文件路径列表
            update_callback: 回调函数，接收 (file_path, icon)
            priority: 加载优先级
        """
        for path in file_paths:
            self._pending_updates[path] = lambda icon, p=path: update_callback(p, icon)
        
        self._loader_thread.add_tasks(file_paths, priority)
    
    def prioritize_visible_items(self, visible_paths: List[str]):
        """
        提升可见项的加载优先级
        
        Args:
            visible_paths: 可见区域的文件路径列表
        """
        # 清空当前队列，重新按优先级添加
        self._loader_thread.clear_tasks()
        
        # 优先加载可见区域
        for path in visible_paths:
            self._loader_thread.add_task(path, self.PRIORITY_VISIBLE)
    
    def _on_icon_loaded(self, file_path: str, icon: QIcon):
        """图标加载完成"""
        # 执行回调
        if file_path in self._pending_updates:
            callback = self._pending_updates.pop(file_path)
            callback(icon)
        
        # 发送信号
        self.icon_ready.emit(file_path, icon)
    
    def clear_cache(self):
        """清空缓存"""
        self._loader_thread._cache.clear()
    
    def stop(self):
        """停止加载器"""
        self._loader_thread.stop()
        self._loader_thread.wait(2000)
        if self._loader_thread.isRunning():
            self._loader_thread.terminate()
    
    def __del__(self):
        """析构函数"""
        self.stop()


# 全局加载器实例
_global_loader: Optional[AsyncIconLoader] = None


def get_async_icon_loader() -> AsyncIconLoader:
    """获取全局异步图标加载器"""
    global _global_loader
    if _global_loader is None:
        _global_loader = AsyncIconLoader()
    return _global_loader


def init_async_icon_loader():
    """初始化全局异步图标加载器"""
    global _global_loader
    if _global_loader is None:
        _global_loader = AsyncIconLoader()


def shutdown_async_icon_loader():
    """关闭全局异步图标加载器"""
    global _global_loader
    if _global_loader:
        _global_loader.stop()
        _global_loader = None
