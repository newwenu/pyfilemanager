from PySide6.QtWidgets import QTreeWidgetItem
import os

class FileOperationHandler:
    """独立处理打开操作的模块（解耦UI与业务逻辑）"""
    def __init__(self, main_window):
        self.main_window = main_window  # 主窗口引用（仅用于更新UI）

    def open_selected_item(self, item: QTreeWidgetItem = None):
        """统一处理文件/文件夹打开逻辑（支持传入指定列表项）"""
        # 若未传入item，取当前选中项
        if not item:
            selected_items = self.main_window.file_list.selectedItems()
            if not selected_items:
                return
            item = selected_items[0]

        # 从列表项中获取文件路径（假设路径存储在 UserRole 中）
        # file_path = item.data(0, Qt.UserRole)
        filename = item.text(0)
        file_path = os.path.normpath(os.path.join(self.main_window.current_path, filename))
        if not file_path:
            return

        if os.path.isdir(file_path):
            # 文件夹：更新当前路径并刷新列表
            self.main_window.current_path = file_path
            self.main_window.address_bar.setText(file_path)
            self.main_window.update_filelist()
            self.main_window.last_updated_path = file_path
        else:
            # 文件：用系统默认程序打开
            os.startfile(file_path)
        
        
        