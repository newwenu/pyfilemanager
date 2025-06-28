import os
from PySide6.QtCore import QThread, Signal, QObject
from utils.file_utils import should_show  # 复用现有过滤函数
# from utils.logging_config import get_logger
# logger = get_logger(__name__)

class FileListLoaderThread(QThread):
    """异步扫描目录的线程类"""
    list_loaded = Signal(list)  # 发送扫描结果（文件信息列表）
    error_occurred = Signal(str)  # 新增信号：发送错误信息
    def __init__(self, path: str, show_hidden: bool):
        super().__init__()
        self.path = path
        self.show_hidden = show_hidden
        self._is_running = True  # 终止标记
        
    def run(self):
        """核心：异步扫描目录并收集文件信息"""
        # print("FileListLoaderThread started.")
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
        except PermissionError as e:
            self.error_occurred.emit(f"无权限访问目录: {self.path}")  # 发射权限错误
            # print("warn:无权限访问目录:", self.path)
            self.list_loaded.emit([])
        except Exception as e:
            self.error_occurred.emit(f"扫描目录时出错: {self.path}")  # 异常时发送错误信息
            self.list_loaded.emit([])  # 发送空列表表示加载失败
        

    def stop(self):
        """外部调用终止线程"""
        # print("stop", self.path)
        self._is_running = False
        # print("FileListLoaderThread stopped.")
class FileListLoaderManager(QObject):
    """管理异步扫描线程的管理器（优化）"""
    list_loaded = Signal(list)  # 转发线程的加载完成信号
    error_occurred = Signal(str)  # 新增信号：转发线程的错误信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_threads = {}  # {路径: 线程对象}
        self.all_threads = set()  # 新增：记录所有未完成的线程（无论路径）
        
    def start_load(self, path: str, show_hidden: bool):
        """启动异步扫描（优化：增加路径冷却和重复加载限制）"""
        # print("start_load", path)
        self.stop_all()
        # 不要提前 return，确保所有线程都能被 stop
        # if path in self.active_threads:
        #     return

        thread = FileListLoaderThread(path, show_hidden)
        self.active_threads[path] = thread
        self.all_threads.add(thread)
        # 连接线程的错误信号到管理器的转发信号
        thread.error_occurred.connect(self.error_occurred.emit)  # 直接转发
        thread.list_loaded.connect(lambda lst: self._on_load_finished(path, lst))
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._on_thread_finished(thread, path))
        thread.start()

    def _on_thread_finished(self, thread, path):
        # print(f"[Thread finished] {getattr(thread, 'path', None)}")
        self.all_threads.discard(thread)
        self.active_threads.pop(path, None)

    # 原有 _on_load_finished 和 stop_all 方法保持不变
    def _on_load_finished(self, path: str, file_list: list):
        self.list_loaded.emit(file_list)
        if path in self.active_threads:
            # print(f"[Load finished] {path}")
            # logger.info(f"[Load finished] {path}")
            thread = self.active_threads[path]
            self.all_threads.discard(thread)  # 从全局集合中移除
            del self.active_threads[path]

    def stop_all(self):
        threads = set(self.all_threads) | set(self.active_threads.values())
        for thread in list(threads):
            # logger.info(f"stop_all: {getattr(thread, 'path', None)}")
            # print(f"Calling stop() for thread: {getattr(thread, 'path', None)}")
            thread.stop()
        for thread in list(threads):
            thread.wait(1000)
            if thread.isRunning():
                # get_logger().info(f"Thread not terminated: {getattr(thread, 'path', None)}")
                # print("Thread not terminated:", thread)
                thread.terminate()  # 极端情况强制终止
                thread.wait()  # 等待终止完成
        # self.active_threads.clear()
        # self.all_threads.clear()