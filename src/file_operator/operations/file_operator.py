"""
文件操作器主实现

整合所有文件操作功能，提供统一的文件操作接口
"""
import os
from typing import List, Optional, Callable

from ..core import IFileOperator, OperationResult, FileInfo
from ..clipboard import FileClipboard
from .path_utils import PathUtils
from .copy_operation import CopyOperation
from .move_operation import MoveOperation
from .delete_operation import DeleteOperation
from .rename_operation import RenameOperation
from .folder_operation import FolderOperation


class FileOperator(IFileOperator):
    """文件操作器
    
    提供完整的文件操作功能：
    - 复制/移动/删除文件
    - 重命名文件
    - 创建文件夹
    - 剪贴板管理
    """
    
    def __init__(self):
        self._clipboard = FileClipboard()
        self._path_utils = PathUtils()
        self._copy_op = CopyOperation(self._path_utils)
        self._move_op = MoveOperation(self._path_utils)
        self._delete_op = DeleteOperation()
        self._rename_op = RenameOperation()
        self._folder_op = FolderOperation(self._path_utils)
    
    # ========== 基本文件操作 ==========
    
    def copy(self, sources: List[str], dest: str,
             progress_callback: Optional[Callable[[str, int, int], None]] = None) -> OperationResult:
        """复制文件/文件夹"""
        return self._copy_op.execute(sources, dest, progress_callback)
    
    def move(self, sources: List[str], dest: str,
             progress_callback: Optional[Callable[[str, int, int], None]] = None) -> OperationResult:
        """移动文件/文件夹"""
        return self._move_op.execute(sources, dest, progress_callback)
    
    def delete(self, paths: List[str]) -> OperationResult:
        """删除文件/文件夹（移动到回收站）"""
        return self._delete_op.execute(paths)
    
    def rename(self, path: str, new_name: str) -> OperationResult:
        """重命名文件/文件夹"""
        return self._rename_op.execute(path, new_name)
    
    def create_folder(self, parent_path: str, name: str) -> OperationResult:
        """创建文件夹"""
        return self._folder_op.create(parent_path, name)
    
    # ========== 剪贴板操作 ==========
    
    @property
    def clipboard(self) -> FileClipboard:
        """获取剪贴板对象"""
        return self._clipboard
    
    def copy_to_clipboard(self, paths: List[str]) -> OperationResult:
        """复制到剪贴板"""
        from ..utils.error_messages import resolve_exception, success_message
        
        try:
            self._clipboard.copy(paths)
            content = self._clipboard.get_content()
            return OperationResult(
                success=True,
                message=success_message('clipboard_copy', len(content['paths'])),
                affected_paths=content['paths']
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=resolve_exception(e),
                affected_paths=[],
                error=e
            )
    
    def cut_to_clipboard(self, paths: List[str]) -> OperationResult:
        """剪切到剪贴板"""
        from ..utils.error_messages import resolve_exception, success_message
        
        try:
            self._clipboard.cut(paths)
            content = self._clipboard.get_content()
            return OperationResult(
                success=True,
                message=success_message('clipboard_cut', len(content['paths'])),
                affected_paths=content['paths']
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=resolve_exception(e),
                affected_paths=[],
                error=e
            )
    
    def paste_from_clipboard(self, dest_dir: str) -> OperationResult:
        """从剪贴板粘贴"""
        from ..utils.error_messages import success_message
        
        result = self._clipboard.paste(dest_dir)
        
        # 转换消息为用户友好格式
        if result.success:
            count = len(result.affected_paths)
            result.message = success_message('paste', count)
        
        return result
    
    # ========== 辅助方法 ==========
    
    def get_file_info(self, path: str) -> Optional[FileInfo]:
        """获取文件信息"""
        if not os.path.exists(path):
            return None
        
        stat = os.stat(path)
        return FileInfo(
            path=path,
            name=os.path.basename(path),
            is_dir=os.path.isdir(path),
            size=stat.st_size,
            modified_time=stat.st_mtime
        )
