"""
Tip管理器模块
提供统一的提示管理功能
"""

from .manager import TipManager, tip_manager
from .tip_manager_proxy import TipManagerProxy, show_success, show_error, show_warning, show_info, show_tip, close_all_tips, close_tip_by_id

# 创建全局实例
Manage = TipManagerProxy()

__all__ = [
    'TipManager',
    'tip_manager',
    'TipManagerProxy', 
    'Manage',  # 推荐使用这个
    'show_success', 
    'show_error', 
    'show_warning', 
    'show_info', 
    'show_tip',
    'close_all_tips',
    'close_tip_by_id'
]