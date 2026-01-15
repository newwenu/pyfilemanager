"""
文件工具模块 - 适配新的图标配置系统
提供文件类型判断、文件图标获取等功能
"""
import os
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from image_manager.icon_config_manager import IconConfigManager

class FileIconAdapter:
    """文件图标适配器 - 连接新图标系统与原有文件工具"""
    
    def __init__(self, config_manager: IconConfigManager = None):
        self.config_manager = config_manager or IconConfigManager()
        
        # 为了向后兼容，构建扩展名到类型的映射
        self._build_legacy_mapping()
    
    def _build_legacy_mapping(self):
        """构建向后兼容的映射"""
        self.ext_to_type = {}
        
        # 从新配置系统构建映射
        for mapping in self.config_manager.icon_mappings:
            for rule in mapping.match_rules:
                if rule.type == "extension":
                    for ext in rule.patterns:
                        if not ext:  # 跳过空扩展名
                            continue
                        ext_key = ext.lower()
                        self.ext_to_type[ext_key] = mapping.name
        
        # 添加默认图标类型
        self.ext_to_type["default"] = self.config_manager.default_icon.name
    
    def get_file_type(self, file_path: str) -> str:
        """获取文件类型（兼容原有接口）"""
        return self.config_manager.get_icon_for_file(file_path)
    
    def get_icon_char(self, file_type: str) -> str:
        """获取文件类型对应的字符图标（兼容原有接口）"""
        return self.config_manager.get_char_fallback(file_type)
    
    def get_file_properties(self, file_path: str) -> dict:
        """获取文件属性，用于图标匹配"""
        file_path = Path(file_path)
        properties = {}
        
        # 检查是否为目录
        properties["is_directory"] = file_path.is_dir()
        
        # 检查是否为隐藏文件
        try:
            properties["is_hidden"] = file_path.stat().st_file_attributes & 0x2 != 0
        except AttributeError:
            # 非Windows系统
            properties["is_hidden"] = file_path.name.startswith(".")
        
        # 检查是否为可执行文件
        if os.name == 'nt':  # Windows
            properties["is_executable"] = file_path.suffix.lower() in ['.exe', '.bat', '.cmd', '.com', '.scr']
        else:  # Unix-like
            properties["is_executable"] = os.access(file_path, os.X_OK) and file_path.is_file()
        
        # 检查是否为链接/快捷方式
        properties["is_link"] = file_path.is_symlink() or file_path.suffix.lower() in ['.lnk', '.url']
        
        # 检查文件大小
        if file_path.is_file():
            try:
                properties["size"] = file_path.stat().st_size
            except OSError:
                properties["size"] = 0
        
        return properties
    
    def refresh_config(self):
        """刷新配置（兼容原有接口）"""
        # 重新构建映射
        self._build_legacy_mapping()

# 为了向后兼容，创建全局实例
_icon_adapter = None

def get_icon_adapter() -> FileIconAdapter:
    """获取全局图标适配器实例"""
    global _icon_adapter
    if _icon_adapter is None:
        _icon_adapter = FileIconAdapter()
    return _icon_adapter

# 为了向后兼容，保留原有的函数接口
def get_file_type(file_path: str) -> str:
    """获取文件类型（兼容原有接口）"""
    return get_icon_adapter().get_file_type(file_path)

def get_icon_char(file_type: str) -> str:
    """获取文件类型对应的字符图标（兼容原有接口）"""
    return get_icon_adapter().get_icon_char(file_type)

def get_file_properties(file_path: str) -> dict:
    """获取文件属性"""
    return get_icon_adapter().get_file_properties(file_path)

def refresh_config():
    """刷新配置（兼容原有接口）"""
    get_icon_adapter().refresh_config()

# 为了向后兼容，保留原有的全局变量
def get_ext_to_type() -> Dict[str, str]:
    """获取扩展名到类型的映射（兼容原有接口）"""
    return get_icon_adapter().ext_to_type