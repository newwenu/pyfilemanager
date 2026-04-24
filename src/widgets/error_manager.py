"""
错误提示管理器

提供统一的错误提示接口，支持多种提示方式：
- 非侵入式提示 (TipWidget) - 默认，用于非关键错误
- 模态对话框 (QMessageBox) - 用于关键错误
- 状态栏提示 - 用于轻微提示
"""
from typing import Optional
from PySide6.QtWidgets import QWidget, QMessageBox
from enum import Enum, auto

from tip_manager.tip_manager_proxy import show_error, show_warning, show_info
from core import event_bus


class ErrorLevel(Enum):
    """错误级别"""
    INFO = auto()      # 信息，使用状态栏或轻量提示
    WARNING = auto()   # 警告，使用非侵入式提示
    ERROR = auto()     # 错误，使用非侵入式提示
    CRITICAL = auto()  # 严重错误，使用模态对话框


class ErrorManager:
    """错误提示管理器
    
    统一管理系统中的错误提示，根据错误级别选择合适的提示方式
    """
    
    def __init__(self, parent: QWidget):
        self._parent = parent
        self._translation = getattr(parent, 'translation', {})
    
    def _tr(self, key: str, default: str = "") -> str:
        """获取翻译文本"""
        return self._translation.get(key, default) if self._translation else default
    
    def show(self, message: str, level: ErrorLevel = ErrorLevel.ERROR,
             title: Optional[str] = None, duration: int = 3000) -> None:
        """显示错误提示
        
        Args:
            message: 提示消息
            level: 错误级别
            title: 对话框标题（仅对 CRITICAL 级别有效）
            duration: 显示时长（毫秒，仅对非模态提示有效）
        """
        if level == ErrorLevel.INFO:
            self._show_info(message, duration)
        elif level == ErrorLevel.WARNING:
            self._show_warning(message, duration)
        elif level == ErrorLevel.ERROR:
            self._show_error(message, duration)
        elif level == ErrorLevel.CRITICAL:
            self._show_critical(message, title)
    
    def _show_info(self, message: str, duration: int = 2000) -> None:
        """显示信息提示"""
        # 优先使用状态栏
        try:
            event_bus.ui_update_statusbar.emit(message, duration)
        except:
            # 回退到 tip
            show_info(self._parent, message, duration)
    
    def _show_warning(self, message: str, duration: int = 2500) -> None:
        """显示警告提示"""
        show_warning(self._parent, message, duration)
    
    def _show_error(self, message: str, duration: int = 3000) -> None:
        """显示错误提示（非侵入式）"""
        show_error(self._parent, message, duration)
    
    def _show_critical(self, message: str, title: Optional[str] = None) -> None:
        """显示严重错误（模态对话框）"""
        if not title:
            title = self._tr("error", "错误")
        
        QMessageBox.critical(self._parent, title, message)
    
    # ========== 便捷方法 ==========
    
    def info(self, message: str, duration: int = 2000) -> None:
        """信息提示"""
        self.show(message, ErrorLevel.INFO, duration=duration)
    
    def warning(self, message: str, duration: int = 2500) -> None:
        """警告提示"""
        self.show(message, ErrorLevel.WARNING, duration=duration)
    
    def error(self, message: str, duration: int = 3000) -> None:
        """错误提示"""
        self.show(message, ErrorLevel.ERROR, duration=duration)
    
    def critical(self, message: str, title: Optional[str] = None) -> None:
        """严重错误提示"""
        self.show(message, ErrorLevel.CRITICAL, title=title)


# 全局错误管理器实例
_error_manager: Optional[ErrorManager] = None


def init_error_manager(parent: QWidget) -> ErrorManager:
    """初始化全局错误管理器"""
    global _error_manager
    _error_manager = ErrorManager(parent)
    return _error_manager


def get_error_manager() -> Optional[ErrorManager]:
    """获取全局错误管理器"""
    return _error_manager


def show_error_tip(message: str, level: ErrorLevel = ErrorLevel.ERROR,
                   title: Optional[str] = None, duration: int = 3000) -> None:
    """显示错误提示的快捷函数"""
    if _error_manager:
        _error_manager.show(message, level, title, duration)
    else:
        # 回退到事件总线
        try:
            if level == ErrorLevel.CRITICAL:
                event_bus.ui_show_error.emit(title or "错误", message)
            else:
                event_bus.ui_update_statusbar.emit(message, duration)
        except:
            pass


# 便捷函数
def info(message: str, duration: int = 2000):
    """信息提示"""
    show_error_tip(message, ErrorLevel.INFO, duration=duration)


def warning(message: str, duration: int = 2500):
    """警告提示"""
    show_error_tip(message, ErrorLevel.WARNING, duration=duration)


def error(message: str, duration: int = 3000):
    """错误提示"""
    show_error_tip(message, ErrorLevel.ERROR, duration=duration)


def critical(message: str, title: Optional[str] = None):
    """严重错误提示"""
    show_error_tip(message, ErrorLevel.CRITICAL, title=title)
