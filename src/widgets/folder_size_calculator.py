import os
from PySide6.QtWidgets import QTreeWidgetItem
from utils.logging_config import get_logger

logger = get_logger(__name__)

class FolderSizeCalculator:
    def __init__(self, file_list_updater):
        self.fm = file_list_updater.fm  # 持有主窗口引用
        self.updater = file_list_updater  # 反向引用 FileListUpdater
        self.folder_threads = {}  # 独立管理线程字典

    def start_folder_size_thread(self, path, item):
        """启动文件夹大小计算线程（使用内部字典存储）"""
        if path in self.folder_threads:  # 避免重复启动
            return
        thread = self.fm.folder_size_manager.start_calculate(path, item)
        if thread is not None:  # 检查线程是否有效
            self.folder_threads[path] = thread  # 仅存储有效线程

    def handle_folder_size_calculation(self, entry, item):
        """处理文件夹大小异步计算及缓存（原 _handle_folder_size_calculation2）"""
        folder_path = entry
        db_result = self.fm.db.get_cached_size(folder_path)  # 通过主窗口访问数据库

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
