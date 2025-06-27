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
        print("FileListLoaderThread stopped.")
class FileListLoaderManager(QObject):
    """管理异步扫描线程的管理器（优化：增加路径加载冷却机制）"""
    list_loaded = Signal(list)  # 转发线程的加载完成信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_threads = {}  # {路径: 线程对象}
        self.all_threads = set()  # 新增：记录所有未完成的线程（无论路径）
        
    def start_load(self, path: str, show_hidden: bool):
        """启动异步扫描（优化：增加路径冷却和重复加载限制）"""
        self.stop_all()
        # 规则2：已有同路径线程运行时跳过（原有逻辑）
        if path in self.active_threads:
            return
        
        # 启动新线程
        thread = FileListLoaderThread(path, show_hidden)
        self.active_threads[path] = thread
        self.all_threads.add(thread)  # 记录所有线程
        thread.list_loaded.connect(lambda lst: self._on_load_finished(path, lst))
        thread.start()
        # print("start_load", path)
        # print(self.all_threads)

    # 原有 _on_load_finished 和 stop_all 方法保持不变
    def _on_load_finished(self, path: str, file_list: list):
        self.list_loaded.emit(file_list)
        if path in self.active_threads:
            thread = self.active_threads[path]
            self.all_threads.discard(thread)  # 从全局集合中移除
            del self.active_threads[path]

    def stop_all(self):
        # 先终止所有线程（非阻塞方式）
        for thread in self.all_threads:
            thread.stop()  # 设置 _is_running=False
        for thread in self.all_threads:
            thread.wait(1000)  # 最多等待1秒
            if thread.isRunning():
                thread.terminate()  # 极端情况强制终止
        self.active_threads.clear()
        self.all_threads.clear()