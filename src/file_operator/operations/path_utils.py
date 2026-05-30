"""
路径工具类

提供路径处理、重名检测等通用功能
"""
import os
from typing import Optional


class PathUtils:
    """路径工具类"""
    
    @staticmethod
    def generate_unique_path(path: str) -> str:
        """生成唯一的文件路径（处理重名）
        
        Args:
            path: 原始路径
            
        Returns:
            唯一的路径，如果不存在重名则返回原路径
        """
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
    
    @staticmethod
    def get_unique_folder_name(parent_path: str, base_name: str) -> str:
        """获取唯一的文件夹名称
        
        Args:
            parent_path: 父目录路径
            base_name: 基础名称
            
        Returns:
            唯一的文件夹完整路径
        """
        target_path = os.path.join(parent_path, base_name)
        
        if not os.path.exists(target_path):
            return target_path
        
        counter = 1
        while True:
            new_name = f"{base_name}({counter})"
            new_path = os.path.join(parent_path, new_name)
            if not os.path.exists(new_path):
                return new_path
            counter += 1
    
    @staticmethod
    def validate_source_exists(path: str) -> Optional[str]:
        """验证源文件是否存在
        
        Args:
            path: 文件路径
            
        Returns:
            如果存在返回None，否则返回错误信息
        """
        if not os.path.exists(path):
            return f"源文件不存在: {path}"
        return None
    
    @staticmethod
    def validate_dest_dir(dest_dir: str) -> Optional[str]:
        """验证目标目录是否有效
        
        Args:
            dest_dir: 目标目录路径
            
        Returns:
            如果有效返回None，否则返回错误信息
        """
        if not os.path.exists(dest_dir):
            return f"目标目录不存在: {dest_dir}"
        if not os.path.isdir(dest_dir):
            return f"目标路径不是目录: {dest_dir}"
        return None
