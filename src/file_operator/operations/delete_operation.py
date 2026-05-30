"""
删除操作实现

支持移动到回收站功能
"""
import os
import sys
from typing import List

from PySide6.QtCore import QFile

from ..core import OperationResult
from ..utils.error_messages import resolve_exception, success_message, partial_failure_message


class DeleteOperation:
    """删除操作类"""
    
    def execute(self, paths: List[str]) -> OperationResult:
        """删除文件/文件夹（移动到回收站）
        
        Args:
            paths: 要删除的路径列表
            
        Returns:
            OperationResult: 操作结果
        """
        affected_paths = []
        errors = []
        
        for path in paths:
            try:
                # 规范化路径（消除..等相对符号）
                path = os.path.normpath(path)
                
                if not os.path.exists(path):
                    raise FileNotFoundError(f"文件不存在: {path}")
                
                # 移动到回收站
                self._move_to_trash(path)
                affected_paths.append(path)
            except Exception as e:
                error_msg = resolve_exception(e, path)
                errors.append(f"{os.path.basename(path)}: {error_msg}")
        
        success = len(errors) == 0
        if success:
            message = success_message('delete', len(affected_paths))
        else:
            message = partial_failure_message('\n'.join(errors))
        
        return OperationResult(
            success=success,
            message=message,
            affected_paths=affected_paths
        )
    
    def _check_desktop_environment(self) -> bool:
        """检查是否有桌面环境（主要用于 Linux）
        
        Returns:
            True 如果有桌面环境
        """
        if sys.platform == "win32" or sys.platform == "darwin":
            return True
        # Linux: 检查 DISPLAY 或 WAYLAND_DISPLAY
        return bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))
    
    def _move_to_trash(self, path: str) -> None:
        """移动文件到回收站
        
        Args:
            path: 文件路径
            
        Raises:
            RuntimeError: Linux 无桌面环境时或 Qt moveToTrash 失败时
        """
        # Linux 无桌面环境检查
        if sys.platform.startswith("linux") and not self._check_desktop_environment():
            raise RuntimeError("无桌面环境，无法移动到回收站（请直接删除或安装桌面环境）")
        
        # 使用 Qt 的 moveToTrash (Qt 5.15+)
        file = QFile(path)
        if not file.moveToTrash():
            raise RuntimeError(f"移动到回收站失败: {path}")
