"""
剪贴板管理模块

管理复制/剪切操作的状态和执行粘贴操作
"""

from .clipboard_action import ClipboardAction
from .clipboard_content import ClipboardContent
from .file_clipboard import FileClipboard

__all__ = [
    'ClipboardAction',
    'ClipboardContent',
    'FileClipboard',
]
