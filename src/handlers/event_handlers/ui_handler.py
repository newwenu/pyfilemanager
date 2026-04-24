"""
UI事件处理器

处理所有与UI更新相关的事件：
- 状态栏更新
- 错误显示（使用非侵入式提示）
- 消息显示
- 视图切换（隐藏文件、大小显示、修改时间）
"""
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMessageBox

from core import get_service
from core.interfaces import FileManagerInterface
from widgets.error_manager import ErrorManager, ErrorLevel

if TYPE_CHECKING:
    pass  # 不再需要，因为使用 Protocol


class UIHandler:
    """UI事件处理器"""

    def __init__(self, file_manager: FileManagerInterface) -> None:
        self.file_manager: FileManagerInterface = file_manager
        self._error_manager = ErrorManager(file_manager)

    def on_update_statusbar(self, message: str, duration: int) -> None:
        """处理状态栏更新事件"""
        self.file_manager.status_bar.showMessage(message, duration)

    def on_show_error(self, title: str, message: str) -> None:
        """处理显示错误事件
        
        根据错误严重程度选择提示方式：
        - 一般错误：使用非侵入式提示
        - 严重错误：使用模态对话框
        """
        # 判断是否为严重错误（根据标题或消息内容）
        critical_keywords = ['严重', '崩溃', '无法恢复', '致命']
        is_critical = any(kw in title or kw in message for kw in critical_keywords)
        
        if is_critical:
            QMessageBox.critical(self.file_manager, title, message)
        else:
            # 使用非侵入式错误提示
            self._error_manager.error(message)

    def on_show_message(self, msg_type: str, message: str) -> None:
        """处理显示消息事件
        
        根据消息类型选择合适的提示方式：
        - error: 非侵入式错误提示
        - warning: 非侵入式警告提示
        - info: 状态栏提示
        """
        if msg_type == "error":
            self._error_manager.error(message)
        elif msg_type == "warning":
            self._error_manager.warning(message)
        else:
            self.file_manager.status_bar.showMessage(message, 3000)

    def on_toggle_hidden(self, state: bool) -> None:
        """处理切换隐藏文件显示事件"""
        self.file_manager.show_hidden = state
        if hasattr(self.file_manager, 'cb_hidden'):
            self.file_manager.cb_hidden.setChecked(state)
        self.file_manager.update_filelist()

    def on_toggle_sizes(self, state: bool) -> None:
        """处理切换显示所有大小事件"""
        self.file_manager.show_all_sizes = state
        if hasattr(self.file_manager, 'cb_show_sizes'):
            self.file_manager.cb_show_sizes.setChecked(state)
        self.file_manager.update_filelist()

    def on_toggle_mtime(self) -> None:
        """处理切换修改时间列显示事件"""
        if self.file_manager.file_list_updater:
            self.file_manager.file_list_updater.show_mtime = not self.file_manager.file_list_updater.show_mtime
            self.file_manager.update_filelist()

    def on_search_start(self, keyword: str) -> None:
        """处理搜索开始事件"""
        search_handler = get_service("search_handler")
        if search_handler:
            search_handler.start_search(keyword)

    def on_search_clear(self) -> None:
        """处理清除搜索事件"""
        search_handler = get_service("search_handler")
        if search_handler:
            search_handler.clear_search()

    def toggle_shortcut_help_dialog(self) -> None:
        """切换快捷键帮助对话框"""
        help_dialog_handler = get_service("help_dialog_handler")
        if help_dialog_handler:
            help_dialog_handler.toggle_dialog()

    def show_settings_dialog(self) -> None:
        """显示设置对话框"""
        settings_manager = get_service("settings_manager")
        if settings_manager:
            settings_manager.show_settings_dialog()
