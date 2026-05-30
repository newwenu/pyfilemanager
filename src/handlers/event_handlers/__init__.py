"""
事件处理器包

提供主窗口的事件处理逻辑分离
"""
from .navigate_handler import NavigateHandler
from .file_operation_handler import FileOperationHandler
from .ui_handler import UIHandler

__all__ = [
    'NavigateHandler',
    'FileOperationHandler',
    'UIHandler',
]
