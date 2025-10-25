"""
Tip管理器模块
提供统一的提示管理功能
"""

from .tip_manager_proxy import TipManagerProxy, show_success, show_error, show_warning, show_info, show_tip

# 创建全局实例
Manage = TipManagerProxy()

__all__ = [
    'TipManagerProxy', 
    'Manage',  # 推荐使用这个
    'show_success', 
    'show_error', 
    'show_warning', 
    'show_info', 
    'show_tip'
]