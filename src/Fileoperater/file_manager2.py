import send2trash
import os
from PySide6.QtWidgets import QMessageBox
from PySide6.QtWidgets import QInputDialog
from PySide6.QtCore import Qt
class FileManager2:
    def __init__(self):
        pass
        
    def create_new_folder(self, parent_widget, current_path, update_callback, error_callback):
        """通用新建文件夹方法"""
        # 修复后的对话框调用
        folder_name, ok = QInputDialog.getText(
            parent_widget,  # 传入有效的父窗口对象
            "新建文件夹",
            "请输入文件夹名称：",
            text="新建文件夹"
        )
        if not ok or not folder_name.strip():
            return

        counter = 1
        target_path = os.path.join(current_path, folder_name)
        while os.path.exists(target_path):
            folder_name = f"新建文件夹({counter})"
            target_path = os.path.join(current_path, folder_name)
            counter += 1

        try:
            os.makedirs(target_path)
            update_callback()  # 通过回调更新文件列表
        except Exception as e:
            error_callback("错误", f"创建失败: {str(e)}")

    def delete_files(self, parent_widget, current_path, selected_items, update_callback, error_callback):
        """通用删除方法"""
        if not selected_items:
            return

        # 统计文件和文件夹数量
        file_count = sum(1 for item in selected_items 
                       if os.path.isfile(os.path.join(current_path, item.text(0))))
        folder_count = len(selected_items) - file_count

        # 确认对话框
        if not QMessageBox.question(
            parent_widget,
            "确认删除",
            f"确定要删除 {file_count} 个文件和 {folder_count} 个文件夹到回收站吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            return

        # 执行删除
        for item in selected_items:
            path = os.path.join(current_path, item.text(0))
            try:
                send2trash.send2trash(path)
            except Exception as e:
                error_callback("错误", f"删除 {item.text(0)} 失败: {str(e)}")
        
        update_callback()  # 触发文件列表更新


