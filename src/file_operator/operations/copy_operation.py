"""
复制操作实现
"""
import os
import shutil
from typing import List, Optional, Callable

from ..core import OperationResult
from ..utils.error_messages import resolve_exception, success_message, partial_failure_message
from .path_utils import PathUtils


class CopyOperation:
    """复制操作类"""
    
    def __init__(self, path_utils: Optional[PathUtils] = None):
        self._path_utils = path_utils or PathUtils()
    
    def execute(self, sources: List[str], dest: str,
                progress_callback: Optional[Callable[[str, int, int], None]] = None) -> OperationResult:
        """复制文件/文件夹
        
        Args:
            sources: 源文件路径列表
            dest: 目标目录
            progress_callback: 进度回调函数 (filename, current, total)
            
        Returns:
            OperationResult: 操作结果
        """
        # 验证目标目录
        error = self._path_utils.validate_dest_dir(dest)
        if error:
            return OperationResult(
                success=False,
                message=error,
                affected_paths=[]
            )
        
        affected_paths = []
        errors = []
        total = len(sources)
        
        for idx, src in enumerate(sources):
            if progress_callback:
                progress_callback(os.path.basename(src), idx + 1, total)
            
            try:
                result = self._copy_single(src, dest)
                affected_paths.append(result)
            except Exception as e:
                error_msg = resolve_exception(e, src)
                errors.append(f"{os.path.basename(src)}: {error_msg}")
        
        success = len(errors) == 0
        if success:
            message = success_message('copy', len(affected_paths))
        else:
            message = partial_failure_message('\n'.join(errors))
        
        return OperationResult(
            success=success,
            message=message,
            affected_paths=affected_paths
        )
    
    def _copy_single(self, src: str, dest_dir: str) -> str:
        """复制单个文件/文件夹
        
        Args:
            src: 源路径
            dest_dir: 目标目录
            
        Returns:
            目标完整路径
            
        Raises:
            FileNotFoundError: 源文件不存在
        """
        error = self._path_utils.validate_source_exists(src)
        if error:
            raise FileNotFoundError(error)
        
        filename = os.path.basename(src)
        dest_path = os.path.join(dest_dir, filename)
        
        # 处理重名
        dest_path = self._path_utils.generate_unique_path(dest_path)
        
        # 执行复制
        if os.path.isfile(src):
            shutil.copy2(src, dest_path)
        else:
            shutil.copytree(src, dest_path)
        
        return dest_path
