"""
文件操作事件处理器

处理所有与文件操作相关的事件：
- 打开选中项
- 复制文件
- 剪切文件
- 粘贴文件
- 删除文件
- 新建文件夹
- 重命名文件
"""
import os
from typing import TYPE_CHECKING, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QInputDialog, QTreeWidgetItem

from core import get_service
from core.interfaces import FileManagerInterface

if TYPE_CHECKING:
    pass  # 不再需要，因为使用 Protocol


class FileOperationHandler:
    """文件操作事件处理器"""

    def __init__(self, file_manager: FileManagerInterface) -> None:
        self.file_manager: FileManagerInterface = file_manager

    def on_open_selected(self) -> None:
        """处理打开选中项事件"""
        file_op_handler = get_service("file_op_handler")
        if file_op_handler:
            file_op_handler.open_selected_item()

    def on_copy_files(self, files: List[str]) -> None:
        """处理复制文件事件（使用路径列表）"""
        file_operator_ui = get_service("file_operator_ui")
        if not file_operator_ui:
            return
        
        if files:
            # 使用传入的路径列表
            file_operator_ui.copy_to_clipboard(files)
        else:
            # 从当前选中的项构建路径列表
            selected_items = self.file_manager.file_list.selectedItems()
            if selected_items:
                file_paths = [
                    os.path.join(self.file_manager.current_path, item.text(0))
                    for item in selected_items
                ]
                file_operator_ui.copy_to_clipboard(file_paths)

    def on_cut_files(self, files: List[str]) -> None:
        """处理剪切文件事件（使用路径列表）"""
        file_operator_ui = get_service("file_operator_ui")
        if not file_operator_ui:
            return
        
        if files:
            # 使用传入的路径列表
            file_operator_ui.cut_to_clipboard(files)
        else:
            # 从当前选中的项构建路径列表
            selected_items = self.file_manager.file_list.selectedItems()
            if selected_items:
                file_paths = [
                    os.path.join(self.file_manager.current_path, item.text(0))
                    for item in selected_items
                ]
                file_operator_ui.cut_to_clipboard(file_paths)

    def on_paste_files(self) -> None:
        """处理粘贴文件事件"""
        file_operator_ui = get_service("file_operator_ui")
        if not file_operator_ui:
            return
        
        current_path = self.file_manager.current_path
        if current_path == "此电脑":
            return
        
        file_operator_ui.paste_from_clipboard(
            current_path,
            on_success=self.file_manager.update_filelist
        )

    def on_delete_files(self, files: List[str]) -> None:
        """处理删除文件事件"""
        file_operator_ui = get_service("file_operator_ui")
        if not file_operator_ui:
            return
        
        if files:
            # 使用传入的文件路径列表
            file_operator_ui.delete_with_confirmation(
                files,
                on_success=self.file_manager.update_filelist
            )
        else:
            # 从当前选中的项构建路径列表
            selected_items = self.file_manager.file_list.selectedItems()
            if selected_items:
                file_paths = [
                    os.path.join(self.file_manager.current_path, item.text(0))
                    for item in selected_items
                ]
                file_operator_ui.delete_with_confirmation(
                    file_paths,
                    on_success=self.file_manager.update_filelist
                )

    def on_new_folder(self, name: str) -> None:
        """处理新建文件夹事件"""
        file_operator_ui = get_service("file_operator_ui")
        if not file_operator_ui:
            return
        
        current_path = self.file_manager.current_path
        if current_path == "此电脑":
            return
        
        file_operator_ui.create_folder_with_dialog(
            current_path,
            on_success=self.file_manager.update_filelist
        )

    def on_rename_file(self, old_path: str, new_name: str) -> None:
        """处理重命名文件事件"""
        file_operator_ui = get_service("file_operator_ui")
        if not file_operator_ui:
            return

        # 如果参数为空，获取当前选中项并显示输入对话框
        if not old_path or not new_name:
            current_item = self.file_manager.file_list.currentItem()
            if not current_item:
                return

            # 获取文件路径
            old_path = current_item.data(0, Qt.UserRole)
            if not old_path:
                old_path = os.path.join(self.file_manager.current_path, current_item.text(0))

            # 显示输入对话框获取新名称
            file_operator_ui.rename_with_dialog(
                old_path,
                current_item.text(0),
                on_success=self.file_manager.update_filelist
            )
        else:
            # 直接使用传入的参数
            result = file_operator_ui.operator.rename(old_path, new_name)
            if result.success:
                self.file_manager.update_filelist()
