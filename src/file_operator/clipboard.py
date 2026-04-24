"""
剪贴板管理模块

管理复制/剪切操作的状态
"""
import os
import shutil
from typing import List
from dataclasses import dataclass, field
from enum import Enum, auto

from .interfaces import IClipboard, OperationResult, OperationType
from .exceptions import FileNotFoundError, FileExistsError


class ClipboardAction(Enum):
    """剪贴板动作类型"""
    COPY = auto()
    CUT = auto()


@dataclass
class ClipboardContent:
    """剪贴板内容"""
    action: ClipboardAction
    paths: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """检查剪贴板内容是否有效"""
        return len(self.paths) > 0 and all(os.path.exists(p) for p in self.paths)
    
    def clear(self):
        """清空内容"""
        self.paths.clear()
        self.action = None


class FileClipboard(IClipboard):
    """文件剪贴板实现"""
    
    def __init__(self):
        self._content = ClipboardContent(action=None, paths=[])
    
    def copy(self, paths: List[str]) -> None:
        """复制文件到剪贴板"""
        valid_paths = [p for p in paths if os.path.exists(p)]
        if not valid_paths:
            raise FileNotFoundError("没有有效的文件路径")
        
        self._content = ClipboardContent(
            action=ClipboardAction.COPY,
            paths=valid_paths
        )
    
    def cut(self, paths: List[str]) -> None:
        """剪切文件到剪贴板"""
        valid_paths = [p for p in paths if os.path.exists(p)]
        if not valid_paths:
            raise FileNotFoundError("没有有效的文件路径")
        
        self._content = ClipboardContent(
            action=ClipboardAction.CUT,
            paths=valid_paths
        )
    
    def paste(self, dest_dir: str) -> OperationResult:
        """粘贴文件到目标目录"""
        if not self._content.is_valid():
            return OperationResult(
                success=False,
                message="剪贴板为空或内容已失效",
                affected_paths=[]
            )
        
        if not os.path.exists(dest_dir):
            return OperationResult(
                success=False,
                message=f"目标目录不存在: {dest_dir}",
                affected_paths=[]
            )
        
        if not os.path.isdir(dest_dir):
            return OperationResult(
                success=False,
                message=f"目标路径不是目录: {dest_dir}",
                affected_paths=[]
            )
        
        affected_paths = []
        errors = []
        
        for src_path in self._content.paths:
            try:
                result = self._paste_single(src_path, dest_dir)
                if result:
                    affected_paths.append(result)
            except Exception as e:
                errors.append(f"{os.path.basename(src_path)}: {str(e)}")
        
        # 剪切操作后清空剪贴板
        if self._content.action == ClipboardAction.CUT:
            self._content.clear()
        
        success = len(errors) == 0
        message = f"成功粘贴 {len(affected_paths)} 个文件" if success else f"部分失败: {'; '.join(errors)}"
        
        return OperationResult(
            success=success,
            message=message,
            affected_paths=affected_paths
        )
    
    def _paste_single(self, src_path: str, dest_dir: str) -> str:
        """粘贴单个文件/文件夹"""
        filename = os.path.basename(src_path)
        dest_path = os.path.join(dest_dir, filename)
        
        # 处理重名
        counter = 1
        base, ext = os.path.splitext(filename)
        while os.path.exists(dest_path):
            new_name = f"{base} ({counter}){ext}"
            dest_path = os.path.join(dest_dir, new_name)
            counter += 1
        
        # 执行复制或移动
        if self._content.action == ClipboardAction.COPY:
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dest_path)
            else:
                shutil.copytree(src_path, dest_path)
        else:  # CUT
            shutil.move(src_path, dest_path)
        
        return dest_path
    
    def clear(self) -> None:
        """清空剪贴板"""
        self._content.clear()
    
    def get_content(self) -> dict:
        """获取剪贴板内容"""
        return {
            "action": self._content.action.name if self._content.action else None,
            "paths": self._content.paths.copy(),
            "is_valid": self._content.is_valid()
        }
    
    @property
    def content(self) -> ClipboardContent:
        """获取剪贴板内容对象"""
        return self._content
