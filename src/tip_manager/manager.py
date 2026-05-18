"""
提示管理器 - 管理多个提示组件
"""
from PySide6.QtCore import QTimer
from shiboken6 import isValid as isdeleted


class TipManager:
    """提示管理器 - 管理多个提示组件"""
    
    def __init__(self):
        self.tips = []  # 存储 (tip_widget, tip_id) 元组
        
    def show_tip(self, parent, text, duration=2000, tip_type="success", tip_id: str = None):
        """显示提示
        
        Args:
            parent: 父窗口
            text: 提示文本
            duration: 显示时长(毫秒)
            tip_type: 提示类型("success", "error", "warning", "info")
            tip_id: 提示的唯一标识，如果提供，相同id的提示会先关闭
        """
        # 延迟导入避免循环导入
        from widgets.tip_widget import TipWidget
        
        # 清理已销毁的提示组件
        self._cleanup_destroyed_tips()
        
        # 如果提供了tip_id，关闭相同id的已有提示
        if tip_id:
            self.close_tip_by_id(tip_id)
        
        # 如果父窗口有顶级窗口，使用顶级窗口作为父窗口
        # 这样可以确保提示显示在最上层，不会被对话框挡住
        if hasattr(parent, 'window'):
            top_level_window = parent.window()
        elif hasattr(parent, 'topLevelWidget'):
            top_level_window = parent.topLevelWidget()
        else:
            top_level_window = parent
            
        # 确保父窗口有效
        if not top_level_window or not isdeleted(top_level_window):
            return
            
        tip = TipWidget(top_level_window, tip_id)
        
        # 设置样式并显示
        tip.show_tip(text, duration, style_type=tip_type)
        self.tips.append((tip, tip_id))
        
        # 清理已隐藏的提示
        QTimer.singleShot(duration + 500, lambda: self._cleanup_tip(tip))
    
    def _cleanup_tip(self, tip):
        """清理已隐藏的提示"""
        for item in self.tips[:]:
            if item[0] == tip:
                try:
                    tip.deleteLater()
                except:
                    pass
                self.tips.remove(item)
                break
    
    def _cleanup_destroyed_tips(self):
        """清理已销毁的提示组件"""
        # 清理列表中已销毁的提示组件
        valid_tips = []
        for tip, tip_id in self.tips:
            try:
                # 检查组件是否还存在
                if tip and not isdeleted(tip):
                    valid_tips.append((tip, tip_id))
                else:
                    # 如果组件已销毁，跳过
                    pass
            except:
                # 如果检查过程中出错，说明组件已无效
                pass
        
        # 更新列表，只保留有效的组件
        self.tips = valid_tips
    
    def close_all_tips(self):
        """关闭所有提示"""
        self._cleanup_destroyed_tips()
        for tip, _ in self.tips[:]:
            try:
                if tip and not isdeleted(tip):
                    tip._hide_tip()
            except:
                pass
        self.tips.clear()
    
    def close_tip_by_id(self, tip_id: str):
        """关闭指定id的提示
        
        Args:
            tip_id: 提示的唯一标识
        """
        self._cleanup_destroyed_tips()
        for tip, tid in self.tips[:]:
            if tid == tip_id:
                try:
                    if tip and not isdeleted(tip):
                        tip._hide_tip()
                except:
                    pass
                # 从列表中移除
                self.tips = [(t, i) for t, i in self.tips if i != tip_id]
                break


# 全局提示管理器实例
tip_manager = TipManager()
