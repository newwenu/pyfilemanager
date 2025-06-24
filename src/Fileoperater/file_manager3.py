from PySide6.QtCore import Qt
import os
import shutil
from PySide6.QtWidgets import QMessageBox, QInputDialog

class FileManager3:
    def __init__(self, main_window):
        self.main_window = main_window
        self.clipboard = {  # 管理剪贴板状态（复制/剪切的文件列表）
            "action": None,  # "copy"或"cut"
            "paths": []       # 待操作的文件/文件夹路径列表
        }

    def copy_files(self, selected_items):
        """复制选中文件到剪贴板"""
        self.clipboard["action"] = "copy"
        self.clipboard["paths"] = [
            os.path.join(self.main_window.current_path, item.text(0)) 
            for item in selected_items
        ]

    def cut_files(self, selected_items):
        """剪切选中文件到剪贴板"""
        self.clipboard["action"] = "cut"
        self.clipboard["paths"] = [
            os.path.join(self.main_window.current_path, item.text(0)) 
            for item in selected_items
        ]

    def paste_files(self):
        """粘贴剪贴板中的文件到当前路径"""
        if not self.clipboard["paths"]:
            return

        current_path = self.main_window.current_path
        if current_path=="此电脑":
            return
        for src_path in self.clipboard["paths"]:
            # 目标路径（自动重命名避免冲突）
            filename = os.path.basename(src_path)
            dest_path = os.path.join(current_path, filename)
            
            # 处理重名
            counter = 1
            while os.path.exists(dest_path):
                base, ext = os.path.splitext(filename)
                dest_path = os.path.join(current_path, f"{base} ({counter}){ext}")
                counter += 1

            try:
                if self.clipboard["action"] == "copy":
                    if os.path.isfile(src_path):
                        shutil.copy2(src_path, dest_path)  # 保留元数据
                    else:
                        shutil.copytree(src_path, dest_path)
                elif self.clipboard["action"] == "cut":
                    shutil.move(src_path, dest_path)
            except Exception as e:
                QMessageBox.critical(self.main_window, "错误", f"操作失败: {str(e)}")
                return

        # 剪切后清空剪贴板路径（复制保留以便重复粘贴）
        if self.clipboard["action"] == "cut":
            self.clipboard["paths"] = []
        self.main_window.update_filelist()  # 刷新文件列表

    def rename_item(self, item):
        """重命名单个文件/文件夹（修正版，直接接收item参数）"""
        if not item:
            return
        # 从item获取完整路径（假设路径存储在UserRole）
        src_path = item.data(0, Qt.UserRole)
        if not src_path:  # 兼容旧逻辑（若未用UserRole存储路径）
            src_path = os.path.join(self.main_window.current_path, item.text(0))

        # 显示输入对话框
        new_name, ok = QInputDialog.getText(
            self.main_window, "重命名", "新名称：", text=item.text(0)
        )
        if not ok or not new_name.strip():
            return

        # 构造目标路径
        dest_path = os.path.join(os.path.dirname(src_path), new_name)
        if os.path.exists(dest_path):
            QMessageBox.warning(self.main_window, "提示", "该名称已存在")
            return

        try:
            os.rename(src_path, dest_path)
            item.setText(0, new_name)  # 直接更新列表显示
            self.main_window.update_filelist()  # 刷新文件列表
        except Exception as e:
            QMessageBox.critical(self.main_window, "错误", f"重命名失败: {str(e)}")        