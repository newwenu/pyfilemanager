"""
主题管理器 - 处理应用程序主题设置
支持自动、浅色、深色主题模式，使用PySide6原生接口
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import Qt
import os
import json


class ThemeManager(QObject):
    """主题管理器类"""
    
    # 主题改变信号
    theme_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_theme = "auto"
        self.system_theme = self._detect_system_theme()
        self._setup_auto_theme_tracking()
        
    def _setup_auto_theme_tracking(self):
        """设置自动主题跟踪"""
        app = QApplication.instance()
        if app and hasattr(app.styleHints(), 'colorSchemeChanged'):
            # 连接系统主题改变信号
            app.styleHints().colorSchemeChanged.connect(self._on_system_theme_changed)
    
    @Slot(Qt.ColorScheme)
    def _on_system_theme_changed(self, color_scheme):
        """系统主题改变时的处理"""
        if color_scheme == Qt.ColorScheme.Dark:
            new_system_theme = "dark"
        elif color_scheme == Qt.ColorScheme.Light:
            new_system_theme = "light"
        else:
            new_system_theme = "light"
        
        if new_system_theme != self.system_theme:
            self.system_theme = new_system_theme
            # 如果当前主题是auto，则应用新的系统主题
            if self.current_theme == "auto":
                self._apply_system_theme()
                self.theme_changed.emit("auto")
    
    def _detect_system_theme(self):
        """检测系统主题"""
        try:
            app = QApplication.instance()
            if app and hasattr(app.styleHints(), 'colorScheme'):
                color_scheme = app.styleHints().colorScheme()
                if color_scheme == Qt.ColorScheme.Dark:
                    return "dark"
                elif color_scheme == Qt.ColorScheme.Light:
                    return "light"
        except Exception as e:
            print(f"检测系统主题失败: {e}")
        
        # 默认返回浅色主题
        return "light"
    
    def apply_theme(self, theme_name):
        """应用主题"""
        if theme_name == self.current_theme:
            return
            
        self.current_theme = theme_name
        
        # 如果主题是 auto，应用系统主题
        if theme_name == "auto":
            self._apply_system_theme()
        else:
            # 应用指定的浅色/深色主题
            self._apply_specific_theme(theme_name)
        
        # 发送主题改变信号
        self.theme_changed.emit(theme_name)
        
    def _apply_system_theme(self):
        """应用系统主题 - 让PySide6自动处理"""
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPalette
        
        app = QApplication.instance()
        if app:
            # 恢复默认调色板，让系统主题生效
            app.setPalette(app.style().standardPalette())
    
    def _apply_specific_theme(self, theme_name):
        """应用指定的主题"""
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPalette, QColor
        from PySide6.QtCore import Qt
        
        app = QApplication.instance()
        if not app:
            return
            
        try:
            if theme_name == "dark":
                # 使用PySide6接口设置深色主题
                self._apply_dark_theme_with_palette(app)
            elif theme_name == "light":
                # 使用PySide6接口设置浅色主题
                self._apply_light_theme_with_palette(app)
            else:
                # 使用系统默认
                self._apply_system_theme()
        except Exception as e:
            print(f"应用主题失败: {e}")
    
    def _apply_dark_theme_with_palette(self, app):
        """使用调色板应用深色主题"""
        from PySide6.QtGui import QPalette, QColor
        from PySide6.QtCore import Qt
        
        dark_palette = QPalette()
        
        # 设置深色主题颜色
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.white)
        
        # 设置禁用状态颜色
        dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
        dark_palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
        dark_palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
        
        app.setPalette(dark_palette)
        
    def _apply_light_theme_with_palette(self, app):
        """使用调色板应用浅色主题"""
        from PySide6.QtGui import QPalette
        
        # 恢复默认调色板
        app.setPalette(app.style().standardPalette())
    
    def get_current_theme(self):
        """获取当前主题"""
        return self.current_theme
    
    def get_actual_theme(self):
        """获取实际应用的主题（考虑auto模式）"""
        if self.current_theme == "auto":
            # 当主题是auto时，返回系统主题
            return self.system_theme
        return self.current_theme