"""
剪贴板内容数据类
"""
import os
from dataclasses import dataclass, field
from typing import List

from .clipboard_action import ClipboardAction


@dataclass
class ClipboardContent:
    """剪贴板内容"""
    action: ClipboardAction = None
    paths: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """检查剪贴板内容是否有效"""
        return len(self.paths) > 0 and all(os.path.exists(p) for p in self.paths)
    
    def clear(self):
        """清空内容"""
        self.paths.clear()
        self.action = None
