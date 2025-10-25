"""
统一的提示管理器
提供简单易用的接口来显示各种类型的提示
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject


class TipManagerProxy(QObject):
    """提示管理器代理类 - 提供统一的提示接口"""
    
    def __init__(self):
        super().__init__()
        self._tip_manager = None
    
    def _get_tip_manager(self):
        """获取tip_manager实例，延迟导入避免循环导入"""
        if self._tip_manager is None:
            from src.widgets.tip_widget import tip_manager
            self._tip_manager = tip_manager
        return self._tip_manager
    
    def show_success(self, parent: QWidget, text: str, duration: int = 2000):
        """显示成功提示
        
        Args:
            parent: 父窗口组件
            text: 提示文本
            duration: 显示时长(毫秒)
        """
        self._get_tip_manager().show_tip(parent, text, duration, "success")
    
    def show_error(self, parent: QWidget, text: str, duration: int = 3000):
        """显示错误提示
        
        Args:
            parent: 父窗口组件
            text: 提示文本
            duration: 显示时长(毫秒)
        """
        self._get_tip_manager().show_tip(parent, text, duration, "error")
    
    def show_warning(self, parent: QWidget, text: str, duration: int = 2500):
        """显示警告提示
        
        Args:
            parent: 父窗口组件
            text: 提示文本
            duration: 显示时长(毫秒)
        """
        self._get_tip_manager().show_tip(parent, text, duration, "warning")
    
    def show_info(self, parent: QWidget, text: str, duration: int = 2000):
        """显示信息提示
        
        Args:
            parent: 父窗口组件
            text: 提示文本
            duration: 显示时长(毫秒)
        """
        self._get_tip_manager().show_tip(parent, text, duration, "info")
    
    def show_tip(self, parent: QWidget, text: str, duration: int = 2000, tip_type: str = "success"):
        """显示自定义提示
        
        Args:
            parent: 父窗口组件
            text: 提示文本
            duration: 显示时长(毫秒)
            tip_type: 提示类型("success", "error", "warning", "info")
        """
        self._get_tip_manager().show_tip(parent, text, duration, tip_type)


# 全局提示管理器代理实例
TipManager = TipManagerProxy()


def show_success(parent: QWidget, text: str, duration: int = 2000):
    """显示成功提示 - 快捷函数"""
    TipManager.show_success(parent, text, duration)


def show_error(parent: QWidget, text: str, duration: int = 3000):
    """显示错误提示 - 快捷函数"""
    TipManager.show_error(parent, text, duration)


def show_warning(parent: QWidget, text: str, duration: int = 2500):
    """显示警告提示 - 快捷函数"""
    TipManager.show_warning(parent, text, duration)


def show_info(parent: QWidget, text: str, duration: int = 2000):
    """显示信息提示 - 快捷函数"""
    TipManager.show_info(parent, text, duration)


def show_tip(parent: QWidget, text: str, duration: int = 2000, tip_type: str = "success"):
    """显示自定义提示 - 快捷函数"""
    TipManager.show_tip(parent, text, duration, tip_type)