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
            from tip_manager.manager import tip_manager
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
    
    def show_tip(self, parent: QWidget, text: str, duration: int = 2000, tip_type: str = "success", tip_id: str = None):
        """显示自定义提示
        
        Args:
            parent: 父窗口组件
            text: 提示文本
            duration: 显示时长(毫秒)
            tip_type: 提示类型("success", "error", "warning", "info")
            tip_id: 提示的唯一标识，如果提供，相同id的提示会先关闭
        """
        self._get_tip_manager().show_tip(parent, text, duration, tip_type, tip_id)
    
    def close_all_tips(self):
        """关闭所有提示"""
        self._get_tip_manager().close_all_tips()
    
    def close_tip_by_id(self, tip_id: str):
        """关闭指定id的提示
        
        Args:
            tip_id: 提示的唯一标识
        """
        self._get_tip_manager().close_tip_by_id(tip_id)



# 全局提示管理器代理实例
TipManager = TipManagerProxy()


def show_success(parent: QWidget, text: str, duration: int = 2000, tip_id: str = None):
    """显示成功提示 - 快捷函数
    
    Args:
        parent: 父窗口组件
        text: 提示文本
        duration: 显示时长(毫秒)
        tip_id: 提示的唯一标识，如果提供，相同id的提示会先关闭
    """
    TipManager.show_tip(parent, text, duration, "success", tip_id)


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


def close_all_tips():
    """关闭所有提示 - 快捷函数"""
    TipManager.close_all_tips()


def close_tip_by_id(tip_id: str):
    """关闭指定id的提示 - 快捷函数
    
    Args:
        tip_id: 提示的唯一标识
    """
    TipManager.close_tip_by_id(tip_id)

