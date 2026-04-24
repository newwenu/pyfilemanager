"""
配置提供者模块 - 提供全局配置访问

使用单例模式，支持：
- 全局配置访问
- 配置变更事件通知
- 动态配置重载
"""
from typing import Any, Callable, Optional
from .event_bus import event_bus


class ConfigProvider:
    """
    配置提供者 - 单例模式
    
    提供全局配置访问，配置变更时自动触发事件
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if ConfigProvider._initialized:
            return
        self._config = {}
        self._observers = {}  # key -> list of callbacks
        ConfigProvider._initialized = True
    
    def load(self, config_dict: dict):
        """
        加载配置
        
        Args:
            config_dict: 配置字典
        """
        self._config = config_dict.copy()
    
    def get(self, key: str, default=None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
        
        Returns:
            配置值或默认值
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any, emit_event: bool = True):
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            emit_event: 是否触发事件
        """
        old_value = self._config.get(key)
        self._config[key] = value
        
        # 只有值改变时才触发事件
        if old_value != value:
            # 通知观察者
            if key in self._observers:
                for callback in self._observers[key]:
                    callback(key, value)
            
            # 触发全局事件
            if emit_event:
                event_bus.config_changed.emit(key, value)
    
    def reload(self, config_dict: dict):
        """
        重新加载配置
        
        Args:
            config_dict: 新的配置字典
        """
        old_config = self._config.copy()
        self._config = config_dict.copy()
        
        # 找出变更的配置并触发事件
        all_keys = set(old_config.keys()) | set(self._config.keys())
        for key in all_keys:
            old_value = old_config.get(key)
            new_value = self._config.get(key)
            if old_value != new_value:
                event_bus.config_changed.emit(key, new_value)
        
        # 触发重载事件
        event_bus.config_reload.emit()
    
    def observe(self, key: str, callback: Callable[[str, Any], None]):
        """
        观察配置变更
        
        Args:
            key: 要观察的配置键
            callback: 回调函数，接收 (key, value) 参数
        """
        if key not in self._observers:
            self._observers[key] = []
        self._observers[key].append(callback)
    
    def unobserve(self, key: str, callback: Callable[[str, Any], None]):
        """
        取消观察配置变更
        
        Args:
            key: 配置键
            callback: 回调函数
        """
        if key in self._observers and callback in self._observers[key]:
            self._observers[key].remove(callback)
    
    def get_all(self) -> dict:
        """获取所有配置"""
        return self._config.copy()
    
    def has(self, key: str) -> bool:
        """检查配置是否存在"""
        return key in self._config


# 全局单例实例
config_provider = ConfigProvider()
