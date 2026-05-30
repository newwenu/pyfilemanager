"""
文件操作异常定义
"""


class FileOperatorError(Exception):
    """文件操作基础异常"""
    pass


class FileNotFoundError(FileOperatorError):
    """文件不存在"""
    pass


class PermissionDeniedError(FileOperatorError):
    """权限不足"""
    pass


class FileExistsError(FileOperatorError):
    """文件已存在"""
    pass


class OperationCancelledError(FileOperatorError):
    """操作被取消"""
    pass


class DiskFullError(FileOperatorError):
    """磁盘空间不足"""
    pass


class PathTooLongError(FileOperatorError):
    """路径过长"""
    pass
