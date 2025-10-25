from PySide6.QtWidgets import QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import QPropertyAnimation, QRect, QTimer, Qt, Property
from PySide6.QtGui import QFont, QPalette, QColor
from shiboken6 import isValid as isdeleted


class TipWidget(QLabel):
    """非侵入式提示组件
    
    使用示例:
        tip = TipWidget(self)
        tip.show_tip("设置已保存", 2000)  # 显示2秒
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self._opacity = 1.0
        self._setup_ui()
        self._setup_animation()
        
    def _setup_ui(self):
        """设置UI样式"""
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(76, 175, 80, 240);
                color: white;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 500;
                border: 1px solid rgba(255, 255, 255, 50);
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # 确保提示显示在最上层，不会被其他窗口挡住
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self.hide()
        
    def _setup_animation(self):
        """设置淡入淡出动画"""
        # 透明度效果
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        # 透明度动画
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(300)
        
        # 位置动画
        self.geometry_animation = QPropertyAnimation(self, b"geometry")
        self.geometry_animation.setDuration(300)
        
    def show_tip(self, text, duration=2000):
        """显示提示
        
        Args:
            text: 提示文本
            duration: 显示时长(毫秒),默认2000毫秒
        """
        # 确保组件状态正常
        if not self.parent_widget or not isdeleted(self):
            return
            
        self.setText(text)
        
        # 获取父窗口的全局几何信息
        parent_global_rect = self.parent_widget.frameGeometry()
        
        # 调整大小以适配文本
        self.adjustSize()
        tip_width = self.width()
        tip_height = self.height()
        
        # 计算美观的位置 - 在父窗口上方居中
        # 使用全局坐标计算，确保位置准确
        screen_geometry = self.parent_widget.screen().geometry()
        
        # 计算居中位置
        x = parent_global_rect.x() + (parent_global_rect.width() - tip_width) // 2
        y = parent_global_rect.y() + parent_global_rect.height() - tip_height - 30  # 底部上方30像素
        
        # 确保提示不会超出屏幕边界
        if x < screen_geometry.x() + 10:
            x = screen_geometry.x() + 10
        elif x + tip_width > screen_geometry.right() - 10:
            x = screen_geometry.right() - tip_width - 10
            
        if y < screen_geometry.y() + 10:
            y = parent_global_rect.y() + 50  # 如果太靠上，显示在父窗口顶部
        elif y + tip_height > screen_geometry.bottom() - 10:
            y = screen_geometry.bottom() - tip_height - 10
        
        # 设置初始位置（稍微偏移用于动画效果）
        start_y = y + 10  # 从下方10像素处开始
        self.setGeometry(x, start_y, tip_width, tip_height)
        
        # 确保提示显示在最上层
        self.raise_()
        self.activateWindow()
        
        # 淡入动画
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()
        
        # 位置动画：从下方滑入
        self.geometry_animation.setStartValue(QRect(x, start_y, tip_width, tip_height))
        self.geometry_animation.setEndValue(QRect(x, y, tip_width, tip_height))
        self.geometry_animation.start()
        
        self.show()
        
        # 设置自动隐藏定时器
        QTimer.singleShot(duration, self._hide_tip)
    
    def _hide_tip(self):
        """隐藏提示"""
        # 淡出动画
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.start()
        
        # 动画完成后隐藏
        QTimer.singleShot(300, self.hide)
    
    def set_opacity(self, opacity):
        """设置透明度"""
        self._opacity = opacity
        if self.opacity_effect:
            self.opacity_effect.setOpacity(opacity)
    
    def get_opacity(self):
        """获取透明度"""
        return self._opacity
    
    opacity = Property(float, get_opacity, set_opacity)


class TipManager:
    """提示管理器 - 管理多个提示组件"""
    
    def __init__(self):
        self.tips = []
        
    def show_tip(self, parent, text, duration=2000, tip_type="success"):
        """显示提示
        
        Args:
            parent: 父窗口
            text: 提示文本
            duration: 显示时长(毫秒)
            tip_type: 提示类型("success", "error", "warning", "info")
        """
        # 清理已销毁的提示组件
        self._cleanup_destroyed_tips()
        
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
            
        tip = TipWidget(top_level_window)
        
        # 根据类型设置样式
        if tip_type == "success":
            tip.setStyleSheet("""
                QLabel {
                    background-color: rgba(76, 175, 80, 240);
                    color: white;
                    border-radius: 8px;
                    padding: 12px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    border: 1px solid rgba(255, 255, 255, 50);
                }
            """)
        elif tip_type == "error":
            tip.setStyleSheet("""
                QLabel {
                    background-color: rgba(244, 67, 54, 240);
                    color: white;
                    border-radius: 8px;
                    padding: 12px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    border: 1px solid rgba(255, 255, 255, 50);
                }
            """)
        elif tip_type == "warning":
            tip.setStyleSheet("""
                QLabel {
                    background-color: rgba(255, 152, 0, 240);
                    color: white;
                    border-radius: 8px;
                    padding: 12px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    border: 1px solid rgba(255, 255, 255, 50);
                }
            """)
        elif tip_type == "info":
            tip.setStyleSheet("""
                QLabel {
                    background-color: rgba(33, 150, 243, 240);
                    color: white;
                    border-radius: 8px;
                    padding: 12px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    border: 1px solid rgba(255, 255, 255, 50);
                }
            """)
        
        tip.show_tip(text, duration)
        self.tips.append(tip)
        
        # 清理已隐藏的提示
        QTimer.singleShot(duration + 500, lambda: self._cleanup_tip(tip))
    
    def _cleanup_tip(self, tip):
        """清理已隐藏的提示"""
        if tip in self.tips:
            try:
                tip.deleteLater()
            except:
                pass
            self.tips.remove(tip)
    
    def _cleanup_destroyed_tips(self):
        """清理已销毁的提示组件"""
        # 清理列表中已销毁的提示组件
        valid_tips = []
        for tip in self.tips:
            try:
                # 检查组件是否还存在
                if tip and not isdeleted(tip):
                    valid_tips.append(tip)
                else:
                    # 如果组件已销毁，跳过
                    pass
            except:
                # 如果检查过程中出错，说明组件已无效
                pass
        
        # 更新列表，只保留有效的组件
        self.tips = valid_tips


# 全局提示管理器实例
tip_manager = TipManager()