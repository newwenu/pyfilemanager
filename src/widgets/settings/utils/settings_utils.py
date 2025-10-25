"""设置工具类"""

from PySide6.QtWidgets import QFileDialog, QMessageBox
import os
import shutil

def browse_background_image(parent, current_path=""):
    """浏览背景图片"""
    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        parent.translation.get("select_background_image", "选择背景图片"),
        current_path,
        "Images (*.png *.jpg *.jpeg *.bmp *.gif *.svg)"
    )
    return file_path if file_path else current_path

def browse_db_path(parent, current_path=""):
    """浏览数据库路径"""
    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        parent.translation.get("select_database_path", "选择数据库路径"),
        current_path,
        "Database Files (*.db)"
    )
    return file_path if file_path else current_path

def clean_cache(parent):
    """清理缓存"""
    # 确认对话框
    reply = QMessageBox.question(
        parent,
        parent.translation.get("confirm_clean_cache", "确认清理缓存"),
        parent.translation.get("confirm_clean_cache_msg", "确定要清理缓存吗？此操作不可撤销。"),
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    
    if reply == QMessageBox.Yes:
        cache_dirs = [
            "userdata/cache",
            "userdata/temp",
            "__pycache__"
        ]
        
        success_count = 0
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                try:
                    if os.path.isfile(cache_dir):
                        os.remove(cache_dir)
                    else:
                        shutil.rmtree(cache_dir)
                    success_count += 1
                except Exception as e:
                    print(f"Failed to clean {cache_dir}: {e}")
        
        # 显示结果
        if success_count > 0:
            QMessageBox.information(
                parent,
                parent.translation.get("clean_cache_success", "清理成功"),
                parent.translation.get("clean_cache_success_msg", f"成功清理了 {success_count} 个缓存目录。")
            )
        else:
            QMessageBox.information(
                parent,
                parent.translation.get("clean_cache_info", "清理完成"),
                parent.translation.get("clean_cache_info_msg", "没有找到可清理的缓存目录。")
            )