"""
文件操作核心模块

提供文件操作的基础接口和数据结构
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
    # 数据类
    'OperationResult',
    'FileInfo',
    # 异常
    'FileOperatorError',
    'FileNotFoundError',
    'PermissionDeniedError',
    'FileExistsError',
    'OperationCancelledError',
    'DiskFullError',
    'PathTooLongError',
]
