"""
文件操作 UI 适配模块

将 FileOperator 与 Qt UI 解耦，提供对话框交互支持
"""

from .ui_adapter import FileOperatorUIAdapter
from .tip_helper import TipHelper

__all__ = [
    'FileOperatorUIAdapter',
    'TipHelper',
]
