"""
剪贴板动作类型枚举
"""
from enum import Enum, auto


class ClipboardAction(Enum):
    """剪贴板动作类型"""
    COPY = auto()
    CUT = auto()
