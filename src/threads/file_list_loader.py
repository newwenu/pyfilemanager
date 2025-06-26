import os
from PySide6.QtCore import QThread, Signal, QObject
from utils.file_utils import should_show  # 复用现有过滤函数

class FileListLoaderThread(QThread):
    """异步扫描目录的线程类"""
    list_loaded = Signal(list)  # 发送扫描结果（文件信息列表）

    def __init__(self, path: str, show_hidden: bool):
        super().__init__()
        self.path = path
        self.show_hidden = show_hidden
        self._is_running = True  # 终止标记

    def run(self):
        """核心：异步扫描目录并收集文件信息"""
        file_list = []
        try:
            with os.scandir(self.path) as entries:
                for entry in entries:
                    if not self._is_running:  # 支持中途终止
                        return
                    if not should_show(entry, self.show_hidden):  # 复用现有过滤逻辑
                        continue
                    # 收集文件元数据（新增“类型”字段）
                    file_info = {
                        "name": entry.name,
                        "path": entry.path,
                        "is_dir": entry.is_dir(),
                        "size": entry.stat().st_size,
                        "mtime": entry.stat().st_mtime
                    }
                    file_list.append(file_info)
            self.list_loaded.emit(file_list)  # 发送扫描结果到主线程
        except Exception as e:
            self.list_loaded.emit([])  # 异常时发送空列表

    def stop(self):
        """外部调用终止线程"""
        self._is_running = False
        self.wait()

class FileListLoaderManager(QObject):
    """管理异步扫描线程的管理器（避免重复扫描同一路径）"""
    list_loaded = Signal(list)  # 转发线程的加载完成信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_threads = {}  # {路径: 线程对象}

    def start_load(self, path: str, show_hidden: bool):
        """启动异步扫描（避免重复加载同一路径）"""
        if path in self.active_threads:
            return  # 已有同路径线程运行，跳过
        thread = FileListLoaderThread(path, show_hidden)
        self.active_threads[path] = thread
        thread.list_loaded.connect(lambda lst: self._on_load_finished(path, lst))
        thread.start()

    def _on_load_finished(self, path: str, file_list: list):
        """扫描完成后的清理与信号转发"""
        self.list_loaded.emit(file_list)  # 通知 FileListUpdater 更新UI
        if path in self.active_threads:
            del self.active_threads[path]  # 移除线程记录

    def stop_all(self):
        """窗口关闭时终止所有未完成的扫描线程"""
        for thread in self.active_threads.values():
            thread.stop()
        self.active_threads.clear()