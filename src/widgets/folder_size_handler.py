import os
from PySide6.QtWidgets import QTreeWidgetItem
from utils.logging_config import get_logger

logger = get_logger(__name__)

class FolderSizeHandler:
    def __init__(self, fm, translation, folder_size_manager, db):
        self.fm = fm
        self.translation = translation
        self.folder_size_manager = folder_size_manager
        self.db = db
        self.folder_threads = {}  # 管理文件夹大小计算线程

    def start_folder_size_thread(self, path, item):
        """启动文件夹大小计算线程（避免重复启动）"""
        if path in self.folder_threads:
            return
        thread = self.folder_size_manager.start_calculate(path, item)
        if thread is not None:
            self.folder_threads[path] = thread  # 仅存储有效线程

    def handle_folder_size_calculation(self, entry, item):
        """处理文件夹大小异步计算及缓存"""
        folder_path = entry
        db_result = self.db.get_cached_size(folder_path)

        if db_result:
            cached_size, db_last_modified = db_result
            try:
                current_last_modified = os.path.getmtime(folder_path)
            except Exception:
                current_last_modified = 0
            
            if current_last_modified != db_last_modified:
                self.start_folder_size_thread(folder_path, item)
            else:
                item.setText(1, cached_size)
        else:
            self.start_folder_size_thread(folder_path, item)

    def clean_old_threads(self):
        """清理未完成的文件夹大小计算线程"""
        for path, thread in list(self.folder_threads.items()):
            thread.stop()
            thread.wait()
            thread.deleteLater()
            del self.folder_threads[path]
