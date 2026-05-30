"""
文件夹操作实现
"""
import os
from typing import Optional

from ..core import OperationResult
from ..utils.error_messages import resolve_exception, success_message
from .path_utils import PathUtils


class FolderOperation:
    """文件夹操作类"""
    
    def __init__(self, path_utils: Optional[PathUtils] = None):
        self._path_utils = path_utils or PathUtils()
    
    def create(self, parent_path: str, name: str) -> OperationResult:
        """创建文件夹
        
        Args:
            parent_path: 父目录路径
            name: 文件夹名称
            
        Returns:
            OperationResult: 操作结果
        """
        if not os.path.exists(parent_path):
            return OperationResult(
                success=False,
                message=f"父目录不存在: {parent_path}",
                affected_paths=[]
            )
        
        if not name or not name.strip():
            return OperationResult(
                success=False,
                message="文件夹名称不能为空",
                affected_paths=[]
            )
        
        # 处理重名
        target_path = self._path_utils.get_unique_folder_name(parent_path, name.strip())
        
        try:
            os.makedirs(target_path)
            return OperationResult(
                success=True,
                message=success_message('create_folder', name=os.path.basename(target_path)),
                affected_paths=[target_path]
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=resolve_exception(e, target_path),
                affected_paths=[],
                error=e
            )
