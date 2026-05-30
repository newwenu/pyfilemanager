"""
提示助手类

处理非侵入式提示和状态栏消息显示
"""
from typing import Optional
from PySide6.QtWidgets import QWidget


class TipHelper:
    """提示助手类
    
    提供统一的提示显示接口，支持 tip_manager 和状态栏回退
    """
    
    def __init__(self, parent_widget: QWidget):
        self._parent = parent_widget
        self._tip_manager = None
    
    def _get_tip_manager(self):
        """延迟获取 tip_manager"""
        if self._tip_manager is None:
            try:
                from tip_manager.tip_manager_proxy import TipManagerProxy
                self._tip_manager = TipManagerProxy()
            except ImportError:
                pass
        return self._tip_manager
    
    def show_success(self, message: str, duration: int = 2000) -> None:
        """显示成功提示（非侵入式）"""
        try:
            from tip_manager.tip_manager_proxy import show_success
            show_success(self._parent, message, duration)
        except ImportError:
            self._show_status_message(message, duration)
    
    def show_error(self, message: str, duration: int = 3000) -> None:
        """显示错误提示（非侵入式）"""
        try:
            from tip_manager.tip_manager_proxy import show_error
            show_error(self._parent, message, duration)
        except ImportError:
            self._show_status_message(message, duration)
    
    def show_warning(self, message: str, duration: int = 2500) -> None:
        """显示警告提示（非侵入式）"""
        try:
            from tip_manager.tip_manager_proxy import show_warning
            show_warning(self._parent, message, duration)
        except ImportError:
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
