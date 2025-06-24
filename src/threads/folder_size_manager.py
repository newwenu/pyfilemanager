from PySide6.QtCore import QObject, Signal, Slot
from .folder_size import FolderSizeThread  

from PySide6.QtWidgets import QTreeWidgetItem
class FolderSizeManager(QObject):
    size_updated = Signal(QTreeWidgetItem, str)  # 定义信号：(列表项, 大小文本)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.folder_threads = {}  # 存储线程

    def start_calculate(self, path: str, item: QTreeWidgetItem):
        """启动文件夹大小计算线程"""
        if path in self.folder_threads:
            return
        thread = FolderSizeThread(path)
        self.folder_threads[path] = thread
        thread.size_updated.connect(lambda path,s,item=item: self._on_size_updated(item, s))
        thread.start()
    # @Slot(QTreeWidgetItem, str)  # 声明槽函数，参数类型为 QTreeWidgetItem 和 int
    def _on_size_updated(self, item, size):
        """线程结果回调"""
        size_str = size
        self.size_updated.emit(item, size_str)  # 触发信号更新UI

    def stop_calculate(self, path: str):
        """停止文件夹大小计算线程"""
        if path in self.folder_threads:
            thread = self.folder_threads[path]
            thread.terminate()  # 终止线程
            thread.wait()  # 等待线程结束
            del self.folder_threads[path]  # 从字典中移除
            