"""
文件操作器主实现

整合所有文件操作功能，提供统一的文件操作接口
使用用户友好的错误消息
"""
import os
import shutil
import send2trash
from typing import List, Optional, Callable
from pathlib import Path

from .interfaces import IFileOperator, OperationResult, FileInfo
from .clipboard import FileClipboard
from .exceptions import (
    FileOperatorError, FileNotFoundError, PermissionDeniedError,
    FileExistsError, DiskFullError
)
from . import error_messages


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
    
    # ========== 基本文件操作 ==========
    
    def copy(self, sources: List[str], dest: str,
             progress_callback: Optional[Callable[[str, int, int], None]] = None) -> OperationResult:
        """复制文件/文件夹"""
        if not os.path.exists(dest):
            return OperationResult(
                success=False,
                message=error_messages.resolve_exception(
                    FileNotFoundError(f"目标目录不存在: {dest}"), dest
                ),
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
                error_msg = error_messages.resolve_exception(e, src)
                errors.append(f"{os.path.basename(src)}: {error_msg}")
        
        success = len(errors) == 0
        if success:
            message = error_messages.success_message('copy', len(affected_paths))
        else:
            message = error_messages.partial_failure_message('\n'.join(errors))
        
        return OperationResult(
            success=success,
            message=message,
            affected_paths=affected_paths
        )
    
    def _copy_single(self, src: str, dest_dir: str) -> str:
        """复制单个文件/文件夹"""
        if not os.path.exists(src):
            raise FileNotFoundError(f"源文件不存在: {src}")
        
        filename = os.path.basename(src)
        dest_path = os.path.join(dest_dir, filename)
        
        # 处理重名
        dest_path = self._generate_unique_path(dest_path)
        
        # 执行复制
        if os.path.isfile(src):
            shutil.copy2(src, dest_path)
        else:
            shutil.copytree(src, dest_path)
        
        return dest_path
    
    def move(self, sources: List[str], dest: str,
             progress_callback: Optional[Callable[[str, int, int], None]] = None) -> OperationResult:
        """移动文件/文件夹"""
        if not os.path.exists(dest):
            return OperationResult(
                success=False,
                message=error_messages.resolve_exception(
                    FileNotFoundError(f"目标目录不存在: {dest}"), dest
                ),
                affected_paths=[]
            )
        
        affected_paths = []
        errors = []
        total = len(sources)
        
        for idx, src in enumerate(sources):
            if progress_callback:
                progress_callback(os.path.basename(src), idx + 1, total)
            
            try:
                result = self._move_single(src, dest)
                affected_paths.append(result)
            except Exception as e:
                error_msg = error_messages.resolve_exception(e, src)
                errors.append(f"{os.path.basename(src)}: {error_msg}")
        
        success = len(errors) == 0
        if success:
            message = error_messages.success_message('move', len(affected_paths))
        else:
            message = error_messages.partial_failure_message('\n'.join(errors))
        
        return OperationResult(
            success=success,
            message=message,
            affected_paths=affected_paths
        )
    
    def _move_single(self, src: str, dest_dir: str) -> str:
        """移动单个文件/文件夹"""
        if not os.path.exists(src):
            raise FileNotFoundError(f"源文件不存在: {src}")
        
        filename = os.path.basename(src)
        dest_path = os.path.join(dest_dir, filename)
        
        # 处理重名
        dest_path = self._generate_unique_path(dest_path)
        
        shutil.move(src, dest_path)
        return dest_path
    
    def delete(self, paths: List[str]) -> OperationResult:
        """删除文件/文件夹（移动到回收站）"""
        affected_paths = []
        errors = []
        
        for path in paths:
            try:
                # 规范化路径（消除..等相对符号）
                path = os.path.normpath(path)
                
                if not os.path.exists(path):
                    raise FileNotFoundError(f"文件不存在: {path}")
                
                # 使用 send2trash 移动到回收站
                send2trash.send2trash(path)
                affected_paths.append(path)
            except Exception as e:
                error_msg = error_messages.resolve_exception(e, path)
                errors.append(f"{os.path.basename(path)}: {error_msg}")
        
        success = len(errors) == 0
        if success:
            message = error_messages.success_message('delete', len(affected_paths))
        else:
            message = error_messages.partial_failure_message('\n'.join(errors))
        
        return OperationResult(
            success=success,
            message=message,
            affected_paths=affected_paths
        )
    
    def rename(self, path: str, new_name: str) -> OperationResult:
        """重命名文件/文件夹"""
        if not os.path.exists(path):
            return OperationResult(
                success=False,
                message=error_messages.resolve_exception(
                    FileNotFoundError(f"文件不存在: {path}"), path
                ),
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
                message=error_messages.resolve_exception(
                    FileExistsError(f"目标名称已存在: {new_name}"), new_name
                ),
                affected_paths=[]
            )
        
        try:
            os.rename(path, new_path)
            return OperationResult(
                success=True,
                message=error_messages.success_message('rename', name=new_name),
                affected_paths=[new_path]
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=error_messages.resolve_exception(e, path),
                affected_paths=[],
                error=e
            )
    
    def create_folder(self, parent_path: str, name: str) -> OperationResult:
        """创建文件夹"""
        if not os.path.exists(parent_path):
            return OperationResult(
                success=False,
                message=error_messages.resolve_exception(
                    FileNotFoundError(f"父目录不存在: {parent_path}"), parent_path
                ),
                affected_paths=[]
            )
        
        if not name or not name.strip():
            return OperationResult(
                success=False,
                message="文件夹名称不能为空",
                affected_paths=[]
            )
        
        # 处理重名
        base_name = name.strip()
        counter = 1
        target_path = os.path.join(parent_path, base_name)
        
        while os.path.exists(target_path):
            target_path = os.path.join(parent_path, f"{base_name}({counter})")
            counter += 1
        
        try:
            os.makedirs(target_path)
            return OperationResult(
                success=True,
                message=error_messages.success_message(
                    'create_folder', 
                    name=os.path.basename(target_path)
                ),
                affected_paths=[target_path]
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=error_messages.resolve_exception(e, target_path),
                affected_paths=[],
                error=e
            )
    
    # ========== 剪贴板操作 ==========
    
    @property
    def clipboard(self) -> FileClipboard:
        """获取剪贴板对象"""
        return self._clipboard
    
    def copy_to_clipboard(self, paths: List[str]) -> OperationResult:
        """复制到剪贴板"""
        try:
            self._clipboard.copy(paths)
            content = self._clipboard.get_content()
            return OperationResult(
                success=True,
                message=error_messages.success_message(
                    'clipboard_copy', 
                    len(content['paths'])
                ),
                affected_paths=content['paths']
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=error_messages.resolve_exception(e),
                affected_paths=[],
                error=e
            )
    
    def cut_to_clipboard(self, paths: List[str]) -> OperationResult:
        """剪切到剪贴板"""
        try:
            self._clipboard.cut(paths)
            content = self._clipboard.get_content()
            return OperationResult(
                success=True,
                message=error_messages.success_message(
                    'clipboard_cut',
                    len(content['paths'])
                ),
                affected_paths=content['paths']
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=error_messages.resolve_exception(e),
                affected_paths=[],
                error=e
            )
    
    def paste_from_clipboard(self, dest_dir: str) -> OperationResult:
        """从剪贴板粘贴"""
        result = self._clipboard.paste(dest_dir)
        
        # 转换消息为用户友好格式
        if result.success:
            count = len(result.affected_paths)
            result.message = error_messages.success_message('paste', count)
        
        return result
    
    # ========== 辅助方法 ==========
    
    def _generate_unique_path(self, path: str) -> str:
        """生成唯一的文件路径（处理重名）"""
        if not os.path.exists(path):
            return path
        
        parent = os.path.dirname(path)
        filename = os.path.basename(path)
        base, ext = os.path.splitext(filename)
        
        counter = 1
        while True:
            new_name = f"{base}({counter}){ext}"
            new_path = os.path.join(parent, new_name)
            if not os.path.exists(new_path):
                return new_path
            counter += 1
    
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
