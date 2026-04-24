from PySide6.QtWidgets import QTreeWidgetItem
import os

# 导入事件总线
from core import event_bus


class FileOperationHandler:
    """文件操作处理器 - 使用事件总线解耦"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def open_selected_item(self, item: QTreeWidgetItem = None):
        """统一处理文件/文件夹打开逻辑（使用事件总线）"""
        # 若未传入item，取当前选中项
        if not item:
            selected_items = self.main_window.file_list.selectedItems()
            if not selected_items:
                return
            item = selected_items[0]

        filename = item.text(0)
        file_path = os.path.normpath(
            os.path.join(self.main_window.current_path, filename)
        )
        if not file_path:
            return

        if os.path.isdir(file_path):
            # 文件夹：使用事件总线导航
            event_bus.navigate_to.emit(file_path)
        else:
            # 文件：用系统默认程序打开
            try:
                os.startfile(file_path)
            except Exception as e:
                # 使用事件总线显示错误
                event_bus.ui_show_error.emit("打开文件失败", str(e))
