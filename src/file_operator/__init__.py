"""
文件操作模块

提供统一的文件操作接口，包括：
- 文件复制、移动、删除、重命名
- 文件夹创建
- 剪贴板管理

使用示例:
    from file_operator import FileOperator, OperationResult
    
    # 创建操作器
    operator = FileOperator()
    
    # 复制文件
    result = operator.copy(["/path/to/file"], "/dest/dir")
    if result.success:
        print(result.message)
    
    # 使用剪贴板
    operator.copy_to_clipboard(["/path/to/file"])
    operator.paste_from_clipboard("/dest/dir")
"""

from .interfaces import (
    IFileOperator,
    IClipboard,
    IFileOperation,
    OperationType,
    OperationStatus,
    OperationResult,
    FileInfo
)
from .file_operator import FileOperator
from .clipboard import FileClipboard, ClipboardContent, ClipboardAction
from .exceptions import (
    FileOperatorError,
    FileNotFoundError,
    PermissionDeniedError,
    FileExistsError,
    OperationCancelledError,
    DiskFullError,
    PathTooLongError
)

__all__ = [
    # 接口
    'IFileOperator',
    'IClipboard',
    'IFileOperation',
    # 枚举
    'OperationType',
    'OperationStatus',
    'ClipboardAction',
    # 数据类
    'OperationResult',
    'FileInfo',
    'ClipboardContent',
    # 实现类
    'FileOperator',
    'FileClipboard',
    # 异常
    'FileOperatorError',
    'FileNotFoundError',
    'PermissionDeniedError',
    'FileExistsError',
    'OperationCancelledError',
    'DiskFullError',
    'PathTooLongError',
]
