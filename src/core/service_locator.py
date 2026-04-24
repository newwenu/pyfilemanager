"""
服务定位器模块 - 提供全局服务访问

使用单例模式，支持：
- 服务注册和获取
- 延迟初始化
- 服务生命周期管理
"""
from typing import Any, Callable, Dict, Optional, Type, TypeVar
from functools import wraps

T = TypeVar('T')


class ServiceLocator:
    """
    服务定位器 - 全局服务访问点
    
    使用示例：
        # 注册服务
        ServiceLocator.register("config", config_provider)
        ServiceLocator.register_factory("database", lambda: DatabaseManager())
        
        # 获取服务
        config = ServiceLocator.get("config")
        db = ServiceLocator.get("database")
    """
    
    _services: Dict[str, Any] = {}
    _factories: Dict[str, Callable[[], Any]] = {}
    _initialized: Dict[str, bool] = {}
    
    @classmethod
    def register(cls, name: str, service: Any) -> None:
        """
        注册服务实例
        
        Args:
            name: 服务名称
            service: 服务实例
        """
        cls._services[name] = service
        cls._initialized[name] = True
    
    @classmethod
    def register_factory(cls, name: str, factory: Callable[[], Any]) -> None:
        """
        注册服务工厂（延迟初始化）
        
        Args:
            name: 服务名称
            factory: 创建服务的工厂函数
        """
        cls._factories[name] = factory
        cls._initialized[name] = False
    
    @classmethod
    def get(cls, name: str, default: Any = None) -> Any:
        """
        获取服务
        
        Args:
            name: 服务名称
            default: 默认值
        
        Returns:
            服务实例或默认值
        """
        # 如果已注册实例，直接返回
        if name in cls._services:
            return cls._services[name]
        
        # 如果注册了工厂且未初始化，创建实例
        if name in cls._factories and not cls._initialized.get(name, False):
            cls._services[name] = cls._factories[name]()
            cls._initialized[name] = True
            return cls._services[name]
        
        return default
    
    @classmethod
    def get_required(cls, name: str) -> Any:
        """
        获取必需的服务
        
        Args:
            name: 服务名称
        
        Returns:
            服务实例
        
        Raises:
            KeyError: 如果服务未注册
        """
        service = cls.get(name)
        if service is None:
            raise KeyError(f"服务未注册: {name}")
        return service
    
    @classmethod
    def has(cls, name: str) -> bool:
        """
        检查服务是否已注册
        
        Args:
            name: 服务名称
        
        Returns:
            是否已注册
        """
        return name in cls._services or name in cls._factories
    
    @classmethod
    def unregister(cls, name: str) -> None:
        """
        注销服务
        
        Args:
            name: 服务名称
        """
        cls._services.pop(name, None)
        cls._factories.pop(name, None)
        cls._initialized.pop(name, None)
    
    @classmethod
    def clear(cls) -> None:
        """清除所有服务"""
        cls._services.clear()
        cls._factories.clear()
        cls._initialized.clear()
    
    @classmethod
    def get_all_service_names(cls) -> list:
        """获取所有服务名称"""
        names = set(cls._services.keys()) | set(cls._factories.keys())
        return sorted(list(names))


def inject(*service_names: str):
    """
    依赖注入装饰器
    
    使用示例：
        @inject("config", "database")
        def my_function(config, database):
            # 使用 config 和 database
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取服务并注入
            services = [ServiceLocator.get(name) for name in service_names]
            return func(*args, *services, **kwargs)
        return wrapper
    return decorator


# 便捷函数
def get_service(name: str, default: Any = None) -> Any:
    """获取服务的便捷函数"""
    return ServiceLocator.get(name, default)


def register_service(name: str, service: Any) -> None:
    """注册服务的便捷函数"""
    ServiceLocator.register(name, service)
