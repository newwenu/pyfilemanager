"""
图标管理器工厂模块
负责创建和管理图标管理器实例，支持新旧系统切换
"""
import os
from typing import Optional
from .icon_config_manager import IconConfigManager
from .icon_manager_new import IconManager
from .icon_manager import create_icon_set

class IconManagerFactory:
    """图标管理器工厂"""
    
    _instance = None
    _config_manager = None
    _icon_manager = None
    _use_new_system = True  # 默认使用新系统
    
    @classmethod
    def get_instance(cls):
        """获取工厂实例（单例模式）"""
        if cls._instance is None:
            cls._instance = IconManagerFactory()
        return cls._instance
    
    def __init__(self):
        """初始化工厂"""
        # 初始化配置管理器
        config_path = "userdata/file-icon-type/icon-config.json"
        fallback_config_path = "userdata/file-icon-type/file-icon_type.json"
        extension_config_path = "userdata/file-icon-type/extensions_collection.json"
        self._config_manager = IconConfigManager(config_path, fallback_config_path)
        self._extension_config_path = extension_config_path
    
    def get_config_manager(self) -> IconConfigManager:
        """获取配置管理器实例"""
        return self._config_manager
    
    def get_icon_manager(self, use_new_system: Optional[bool] = None) -> object:
        """获取图标管理器实例
        
        Args:
            use_new_system: 是否使用新系统，None表示使用当前设置
            
        Returns:
            图标管理器实例
        """
        # 如果指定了使用哪个系统，更新设置
        if use_new_system is not None:
            self._use_new_system = use_new_system
        
        # 如果还没有创建图标管理器，或者需要切换系统
        if self._icon_manager is None:
            if self._use_new_system:
                self._icon_manager = IconManager(self._config_manager, extension_config_path=self._extension_config_path)
            else:
                # 使用旧系统
                self._icon_manager = create_icon_set()
        
        return self._icon_manager
    
    def switch_to_new_system(self):
        """切换到新图标系统"""
        if not self._use_new_system:
            self._use_new_system = True
            self._icon_manager = None  # 重置图标管理器，下次获取时创建新实例
    
    def switch_to_legacy_system(self):
        """切换到旧图标系统"""
        if self._use_new_system:
            self._use_new_system = False
            self._icon_manager = None  # 重置图标管理器，下次获取时创建旧实例
    
    def is_using_new_system(self) -> bool:
        """检查当前是否使用新系统"""
        return self._use_new_system
    
    def refresh_all(self):
        """刷新所有缓存和配置"""
        # 刷新配置管理器
        self._config_manager = IconConfigManager(
            "userdata/file-icon-type/icon-config.json",
            "userdata/file-icon-type/file-icon_type.json"
        )
        
        # 重置图标管理器
        self._icon_manager = None
    
    def refresh_extensions(self) -> bool:
        """刷新扩展名集合"""
        if self._use_new_system and self._icon_manager:
            return self._icon_manager.refresh_extensions()
        return False
    
    def get_extensions_count(self) -> int:
        """获取扩展名集合中的扩展名数量"""
        if self._use_new_system and self._icon_manager:
            return self._icon_manager.get_extensions_count()
        return 0

# 为了向后兼容，提供全局函数
def get_icon_manager(use_new_system: Optional[bool] = None) -> object:
    """获取图标管理器实例（全局函数）"""
    return IconManagerFactory.get_instance().get_icon_manager(use_new_system)

def get_config_manager() -> IconConfigManager:
    """获取配置管理器实例（全局函数）"""
    return IconManagerFactory.get_instance().get_config_manager()

def switch_to_new_icon_system():
    """切换到新图标系统（全局函数）"""
    IconManagerFactory.get_instance().switch_to_new_system()

def switch_to_legacy_icon_system():
    """切换到旧图标系统（全局函数）"""
    IconManagerFactory.get_instance().switch_to_legacy_system()

def is_using_new_icon_system() -> bool:
    """检查当前是否使用新图标系统（全局函数）"""
    return IconManagerFactory.get_instance().is_using_new_system()

def refresh_icon_system():
    """刷新图标系统（全局函数）"""
    IconManagerFactory.get_instance().refresh_all()

def refresh_extensions() -> bool:
    """刷新扩展名集合（全局函数）"""
    return IconManagerFactory.get_instance().refresh_extensions()

def get_extensions_count() -> int:
    """获取扩展名集合中的扩展名数量（全局函数）"""
    return IconManagerFactory.get_instance().get_extensions_count()