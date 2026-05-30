"""
重命名操作实现
"""
import os

from ..core import OperationResult
from ..utils.error_messages import resolve_exception, success_message


class RenameOperation:
    """重命名操作类"""
    
    def execute(self, path: str, new_name: str) -> OperationResult:
        """重命名文件/文件夹
        
        Args:
            path: 原文件路径
            new_name: 新名称
            
        Returns:
            OperationResult: 操作结果
        """
        if not os.path.exists(path):
            return OperationResult(
                success=False,
                message=f"文件不存在: {path}",
                affected_paths=[]
            )
        
        if not new_name or not new_name.strip():
            return OperationResult(
                success=False,
                message="新名称不能为空",
                affected_paths=[]
            )
        
        parent_dir = os.path.dirname(path)
        new_path = os.path.join(parent_dir, new_name.strip())
        
        if os.path.exists(new_path):
            return OperationResult(
                success=False,
                message=f"目标名称已存在: {new_name}",
                affected_paths=[]
            )
        
        try:
            os.rename(path, new_path)
            return OperationResult(
                success=True,
                message=success_message('rename', name=new_name),
                affected_paths=[new_path]
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=resolve_exception(e, path),
                affected_paths=[],
                error=e
            )
