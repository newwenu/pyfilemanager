import os
from PySide6.QtCore import QThread, Signal, QObject
from utils.file_utils import should_show  # 复用现有过滤函数
from utils.logging_config import get_logger
logger = get_logger(__name__)

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
        """核心：异步扫描目录并收集文件信息（添加调试打印）"""
        file_list = []
        try:
            with os.scandir(self.path) as entries:
                for entry in entries:
                    if not self._is_running:
                        # print(f"[调试] 扫描终止：{self.path}（用户中断）")  # 新增：中断提示
                        return
                    if not should_show(entry, self.show_hidden):
                        continue
                    # 新增：判断文件夹是否有子目录（简化逻辑，仅检查是否有至少一个子项）
                    has_children = False
                    if entry.is_dir():
                        try:
                            # 快速判断是否有子项（避免递归扫描）
                            with os.scandir(entry.path) as sub_entries:
                                has_children = any(sub_entries)  # 存在至少一个子项
                        except PermissionError:
                            has_children = False  # 无权限时默认无
                    # 补充has_children字段到文件信息
                    file_info = {
                        "name": entry.name,
                        "path": entry.path,
                        "is_dir": entry.is_dir(),
                        "size": entry.stat().st_size,
                        "mtime": entry.stat().st_mtime,
                        "has_children": has_children  # 新增字段
                    }
                    file_list.append(file_info)
            # print(f"[调试] 子目录扫描完成，路径：{self.path}，扫描到 {len(file_list)} 个文件/文件夹")  # 新增：扫描结果提示
            self.list_loaded.emit(file_list)
        except PermissionError as e:
            # print(f"[调试] 无权限访问目录：{self.path}（错误：{str(e)}）")  # 新增：权限错误提示
            self.error_occurred.emit(f"无权限访问目录: {self.path}")
            self.list_loaded.emit([])
        except Exception as e:
            # print(f"[调试] 扫描目录时出错：{self.path}（错误：{str(e)}）")  # 新增：异常提示
            self.error_occurred.emit(f"扫描目录时出错: {self.path}")
            self.list_loaded.emit([])

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

    def start_load_subdir(self, parent_path: str, show_hidden: bool, callback):
        """启动子目录异步加载（新增方法）"""
        # 创建专用线程加载子目录（路径为parent_path）
        loader = FileListLoaderThread(parent_path, show_hidden)
        loader.list_loaded.connect(callback)  # 加载完成后触发回调
        loader.start()
        # 可选：管理线程生命周期（避免内存泄漏）
        self.all_threads.add(loader)
        self.active_threads[parent_path] = loader
        return loader

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