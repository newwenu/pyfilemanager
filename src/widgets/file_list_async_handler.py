from PySide6.QtWidgets import QTreeWidgetItem
from utils.sort_utils import sort_file_list
from utils.logging_config import get_logger
import weakref
from PySide6.QtCore import Qt

logger = get_logger(__name__)

class FileListAsyncHandler:
    def __init__(self, file_list_updater):
        self.fm = file_list_updater.fm  # 持有主窗口引用
        self.file_list = file_list_updater.file_list
        self.translation = file_list_updater.translation
        self.header_handler = file_list_updater.header_handler
        self.loaded_subdirs = set()  # 从原类迁移的状态

    def on_folder_expanded(self, item):
        """原on_folder_expanded方法迁移至此"""
        folder_path = item.data(0, Qt.UserRole)
        if not folder_path:
            return
        
        if folder_path in self.loaded_subdirs:
            if item.childCount() > 0:
                item.setExpanded(True)
                return
        
        item.setText(1, self.translation.get("calculating", "计算中..."))
        weak_item = weakref.ref(item)
        self.fm.file_list_updater.file_list_loader.start_load_subdir(
            parent_path=folder_path,
            show_hidden=self.fm.show_hidden,
            callback=lambda sub_list: self._on_subdir_loaded(sub_list, weak_item)
        )

    def _on_subdir_loaded(self, sub_list: list, weak_parent_item):
        """原_on_subdir_loaded方法迁移至此"""
        parent_item = weak_parent_item()
        if not parent_item:
            return
        
        parent_path = parent_item.data(0, Qt.UserRole)
        self.loaded_subdirs.add(parent_path)
        parent_item.setText(1, self.translation.get("folder", "<文件夹>"))
        parent_item.takeChildren()  # 清除旧子节点
        
        # 使用当前排序规则排序子目录
        sorted_sub_list = sort_file_list(
            sub_list,
            sort_key=self.header_handler.current_sort_key,
            reverse=self.header_handler.current_reverse
        )
        
        for sub_info in sorted_sub_list:
            sub_item = self.fm.file_list_updater._create_list_item_from_info_child(sub_info)
            self.fm.file_list_updater._apply_hidden_style(sub_item, sub_info["path"])
            parent_item.addChild(sub_item)
        
        parent_item.setExpanded(True)
