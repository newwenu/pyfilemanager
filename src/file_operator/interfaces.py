"""
文件操作接口定义

提供文件操作的抽象接口，便于测试和替换实现
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Callable
from dataclasses import dataclass
from enum import Enum, auto


class OperationType(Enum):
    """操作类型"""
    COPY = auto()
    MOVE = auto()
    DELETE = auto()
    RENAME = auto()
    CREATE_FOLDER = auto()


class OperationStatus(Enum):
    """操作状态"""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class OperationResult:
    """操作结果"""
    success: bool
    message: str
    affected_paths: List[str]
    error: Optional[Exception] = None


@dataclass
class FileInfo:
    """文件信息"""
    path: str
    name: str
    is_dir: bool
    size: int
    modified_time: float


class IFileOperation(ABC):
    """文件操作接口"""
    
    @property
    @abstractmethod
    def operation_type(self) -> OperationType:
        """操作类型"""
        pass
    
    @abstractmethod
    def execute(self) -> OperationResult:
        """执行操作"""
        pass
    
    @abstractmethod
    def undo(self) -> OperationResult:
        """撤销操作"""
        pass


class IClipboard(ABC):
    """剪贴板接口"""
    
    @abstractmethod
    def copy(self, paths: List[str]) -> None:
        """复制文件到剪贴板"""
        pass
    
    @abstractmethod
    def cut(self, paths: List[str]) -> None:
        """剪切文件到剪贴板"""
        pass
    
    @abstractmethod
    def paste(self, dest_dir: str) -> OperationResult:
        """粘贴文件到目标目录"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空剪贴板"""
        pass
    
    @abstractmethod
    def get_content(self) -> dict:
        """获取剪贴板内容"""
        pass


class IFileOperator(ABC):
    """文件操作器接口"""
    
    @abstractmethod
    def copy(self, sources: List[str], dest: str, 
             progress_callback: Optional[Callable] = None) -> OperationResult:
        """复制文件"""
        pass
    
    @abstractmethod
    def move(self, sources: List[str], dest: str,
             progress_callback: Optional[Callable] = None) -> OperationResult:
        """移动文件"""
        pass
    
    @abstractmethod
    def delete(self, paths: List[str]) -> OperationResult:
        """删除文件（到回收站）"""
        pass
    
    @abstractmethod
    def rename(self, path: str, new_name: str) -> OperationResult:
        """重命名文件"""
        pass
    
    @abstractmethod
    def create_folder(self, parent_path: str, name: str) -> OperationResult:
        """创建文件夹"""
        pass
