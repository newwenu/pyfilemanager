"""
文件操作 UI 适配器

将 FileOperator 与 Qt UI 解耦，提供对话框交互支持
使用非侵入式提示替代模态对话框
"""
from typing import List, Callable, Optional
from PySide6.QtWidgets import QMessageBox, QInputDialog, QWidget
from PySide6.QtCore import Qt

from .file_operator import FileOperator
from .interfaces import OperationResult


class FileOperatorUIAdapter:
    """文件操作 UI 适配器
    
    将底层文件操作与 Qt UI 结合，提供：
    - 确认对话框（关键操作）
    - 输入对话框
    - 非侵入式状态反馈
    """
    
    def __init__(self, file_operator: FileOperator, parent_widget: QWidget):
        self._operator = file_operator
        self._parent = parent_widget
        self._translation = getattr(parent_widget, 'translation', {})
        
        # 延迟导入 tip_manager 避免循环导入
        self._tip_manager = None
    
    def _get_tip_manager(self):
        """延迟获取 tip_manager"""
        if self._tip_manager is None:
            from tip_manager.tip_manager_proxy import TipManagerProxy
            self._tip_manager = TipManagerProxy()
        return self._tip_manager
    
    def _tr(self, key: str, default: str = "") -> str:
        """获取翻译文本"""
        return self._translation.get(key, default) if self._translation else default
    
    # ========== 带 UI 的文件操作 ==========
    
    def create_folder_with_dialog(self, parent_path: str,
                                  on_success: Optional[Callable] = None) -> None:
        """通过对话框创建文件夹"""
        folder_name, ok = QInputDialog.getText(
            self._parent,
            self._tr("new_folder", "新建文件夹"),
            self._tr("new_folder_tip", "请输入文件夹名称："),
            text=self._tr("new_folder", "新建文件夹")
        )
        
        if not ok or not folder_name.strip():
            return
        
        result = self._operator.create_folder(parent_path, folder_name)
        self._handle_result(result, on_success)
    
    def delete_with_confirmation(self, paths: List[str],
                                 file_count: int = 0,
                                 folder_count: int = 0,
                                 on_success: Optional[Callable] = None) -> None:
        """带确认对话框的删除操作"""
        if not paths:
            return
        
        # 构建确认消息
        if file_count == 0 and folder_count == 0:
            # 自动统计
            file_count = sum(1 for p in paths if not os.path.isdir(p))
            folder_count = len(paths) - file_count
        
        confirm_msg = self._tr(
            "confirm_delete_message",
            "确定要删除 {file_count} 个文件和 {folder_count} 个文件夹到回收站吗？"
        ).format(file_count=file_count, folder_count=folder_count)
        
        reply = QMessageBox.question(
            self._parent,
            self._tr("confirm_delete", "确认删除"),
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        result = self._operator.delete(paths)
        self._handle_result(result, on_success)
    
    def rename_with_dialog(self, old_path: str,
                           current_name: str,
                           on_success: Optional[Callable] = None) -> None:
        """通过对话框重命名"""
        new_name, ok = QInputDialog.getText(
            self._parent,
            self._tr("rename", "重命名"),
            self._tr("new_name", "新名称："),
            text=current_name
        )
        
        if not ok or not new_name.strip() or new_name.strip() == current_name:
            return
        
        result = self._operator.rename(old_path, new_name.strip())
        
        # 特殊处理：名称已存在时显示警告而非错误
        if not result.success and "已存在" in result.message:
            self._show_warning(result.message)
        else:
            self._handle_result(result, on_success)
    
    def copy_to_clipboard(self, paths: List[str],
                          on_success: Optional[Callable] = None) -> None:
        """复制到剪贴板并显示状态"""
        result = self._operator.copy_to_clipboard(paths)
        self._handle_result(result, on_success)
    
    def cut_to_clipboard(self, paths: List[str],
                         on_success: Optional[Callable] = None) -> None:
        """剪切到剪贴板并显示状态"""
        result = self._operator.cut_to_clipboard(paths)
        self._handle_result(result, on_success)
    
    def paste_from_clipboard(self, dest_dir: str,
                             on_success: Optional[Callable] = None) -> None:
        """从剪贴板粘贴"""
        result = self._operator.paste_from_clipboard(dest_dir)
        self._handle_result(result, on_success)
    
    # ========== 结果处理（使用非侵入式提示） ==========
    
    def _handle_result(self, result: OperationResult,
                       on_success: Optional[Callable] = None) -> None:
        """处理操作结果"""
        if result.success:
            self._show_success(result.message)
            if on_success:
                on_success()
        else:
            self._show_error(result.message)
    
    def _show_success(self, message: str, duration: int = 2000) -> None:
        """显示成功提示（非侵入式）"""
        try:
            from tip_manager.tip_manager_proxy import show_success
            show_success(self._parent, message, duration)
        except ImportError:
            # 回退到状态栏
            self._show_status_message(message, duration)
    
    def _show_error(self, message: str, duration: int = 3000) -> None:
        """显示错误提示（非侵入式）"""
        try:
            from tip_manager.tip_manager_proxy import show_error
            show_error(self._parent, message, duration)
        except ImportError:
            # 回退到状态栏
            self._show_status_message(message, duration)
    
    def _show_warning(self, message: str, duration: int = 2500) -> None:
        """显示警告提示（非侵入式）"""
        try:
            from tip_manager.tip_manager_proxy import show_warning
            show_warning(self._parent, message, duration)
        except ImportError:
            # 回退到状态栏
            self._show_status_message(message, duration)
    
    def _show_status_message(self, message: str, duration: int = 3000) -> None:
        """显示状态栏消息（通过事件总线）"""
        try:
            from core import event_bus
            event_bus.ui_update_statusbar.emit(message, duration)
        except ImportError:
            # 回退到直接设置状态栏
            if hasattr(self._parent, 'status_bar'):
                self._parent.status_bar.showMessage(message, duration)
    
    # ========== 属性访问 ==========
    
    @property
    def operator(self) -> FileOperator:
        """获取底层文件操作器"""
        return self._operator


import os
