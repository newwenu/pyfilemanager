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

目录结构:
    core/           - 核心接口和异常定义
    operations/     - 具体操作实现
    clipboard/      - 剪贴板管理
    ui/             - UI适配器
    utils/          - 工具函数
"""

# 从 core 导入接口和数据类
from .core import (
    IFileOperator,
    IClipboard,
    IFileOperation,
    OperationType,
    OperationStatus,
    OperationResult,
    FileInfo,
    FileOperatorError,
    FileNotFoundError,
    PermissionDeniedError,
    FileExistsError,
    OperationCancelledError,
    DiskFullError,
    PathTooLongError
)

# 从 operations 导入主操作器
from .operations import FileOperator

# 从 clipboard 导入剪贴板相关
from .clipboard import (
    FileClipboard,
    ClipboardContent,
    ClipboardAction
)

# 从 ui 导入适配器
from .ui import FileOperatorUIAdapter

# 从 utils 导入错误消息模块（保持向后兼容）
from .utils import error_messages

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
    'FileOperatorUIAdapter',
    # 异常
    'FileOperatorError',
    'FileNotFoundError',
    'PermissionDeniedError',
    'FileExistsError',
    'OperationCancelledError',
    'DiskFullError',
    'PathTooLongError',
]
