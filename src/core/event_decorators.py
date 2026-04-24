"""
事件装饰器模块 - 简化事件总线的使用

提供装饰器来简化事件的订阅和发布
"""
from functools import wraps
from typing import Callable, Optional
from . import event_bus


def on_event(event_name: str):
    """
    事件订阅装饰器
    
    使用示例：
        @on_event("navigate_to")
        def handle_navigate(path: str):
            print(f"导航到: {path}")
    
    Args:
        event_name: 事件名称
    """
    def decorator(func: Callable):
        # 获取事件信号
        signal = getattr(event_bus, event_name, None)
        if signal:
            # 连接信号
            signal.connect(func)
        return func
    return decorator


def emit_event(event_name: str):
    """
    事件发布装饰器
    
    使用示例：
        @emit_event("navigate_refresh")
        def do_something():
            # 执行某些操作
            pass
    
    Args:
        event_name: 事件名称
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # 获取事件信号
            signal = getattr(event_bus, event_name, None)
            if signal:
                # 发射信号
                signal.emit()
            return result
        return wrapper
    return decorator


def emit_after(event_name: str, *emit_args, **emit_kwargs):
    """
    在函数执行后发射事件
    
    使用示例：
        @emit_after("ui_update_statusbar", "操作完成", 3000)
        def do_operation():
            # 执行操作
            pass
    
    Args:
        event_name: 事件名称
        *emit_args: 发射事件的参数
        **emit_kwargs: 发射事件的关键字参数
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # 获取事件信号
            signal = getattr(event_bus, event_name, None)
            if signal:
                # 发射信号
                signal.emit(*emit_args, **emit_kwargs)
            return result
        return wrapper
    return decorator


class EventMixin:
    """
    事件混入类
    
    为类提供便捷的事件订阅和发布方法
    
    使用示例：
        class MyClass(EventMixin):
            def __init__(self):
                super().__init__()
                self.subscribe("navigate_to", self.on_navigate)
            
            def on_navigate(self, path: str):
                print(f"导航到: {path}")
            
            def do_something(self):
                self.emit("navigate_refresh")
    """
    
    def __init__(self):
        self._event_connections = []
    
    def subscribe(self, event_name: str, handler: Callable):
        """
        订阅事件
        
        Args:
            event_name: 事件名称
            handler: 事件处理函数
        """
        signal = getattr(event_bus, event_name, None)
        if signal:
            signal.connect(handler)
            self._event_connections.append((signal, handler))
    
    def unsubscribe(self, event_name: str, handler: Callable):
        """
        取消订阅事件
        
        Args:
            event_name: 事件名称
            handler: 事件处理函数
        """
        signal = getattr(event_bus, event_name, None)
        if signal:
            signal.disconnect(handler)
            if (signal, handler) in self._event_connections:
                self._event_connections.remove((signal, handler))
    
    def emit(self, event_name: str, *args, **kwargs):
        """
        发射事件
        
        Args:
            event_name: 事件名称
            *args: 事件参数
            **kwargs: 事件关键字参数
        """
        signal = getattr(event_bus, event_name, None)
        if signal:
            signal.emit(*args, **kwargs)
    
    def disconnect_all(self):
        """断开所有事件连接"""
        for signal, handler in self._event_connections:
            try:
                signal.disconnect(handler)
            except:
                pass
        self._event_connections.clear()
