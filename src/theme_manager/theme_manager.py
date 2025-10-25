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
        self.current_theme = None  # 初始状态设为None，确保首次应用时能正确执行
        self.system_theme = self._detect_system_theme()
        self.main_window = parent  # 保存主窗口引用
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
                else:
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
        """应用系统主题 - 使用PySide6原生的系统主题色"""
        from PySide6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app:
            # PySide6 会自动根据系统主题设置调色板，我们只需要获取当前调色板
            current_palette = app.palette()
            
            # 覆写主窗口的sys_bg变量为当前系统主题色
            self._override_main_window_sys_bg(current_palette.color(current_palette.ColorRole.Window))
    
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
        """使用PySide6原生接口应用深色主题"""
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QPalette, QColor
        
        # 使用标准的深色主题配置
        try:
            # 创建深色主题调色板 - 使用标准的深色主题颜色
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
            dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.white)
            dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(42, 42, 42))
            dark_palette.setColor(QPalette.ColorRole.Text, Qt.white)
            dark_palette.setColor(QPalette.ColorRole.Button, QColor(40, 40, 40))
            dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.white)
            dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.red)
            dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.black)
            
            app.setPalette(dark_palette)
            
            # 覆写主窗口的sys_bg变量为深色主题颜色
            self._override_main_window_sys_bg(dark_palette.color(QPalette.ColorRole.Window))
            
        except Exception as e:
            print(f"应用深色主题失败: {e}")
            # 如果失败，使用系统默认调色板作为回退
            app.setPalette(app.style().standardPalette())
            self._override_main_window_sys_bg(app.palette().color(QPalette.ColorRole.Window))
    
    def _apply_light_theme_with_palette(self, app):
        """使用PySide6原生接口应用浅色主题"""
        from PySide6.QtGui import QPalette
        
        # 使用系统默认调色板作为浅色主题
        try:
            # 恢复系统默认调色板（浅色主题）
            system_palette = app.style().standardPalette()
            app.setPalette(system_palette)
            
            # 覆写主窗口的sys_bg变量为浅色主题颜色
            self._override_main_window_sys_bg(system_palette.color(QPalette.ColorRole.Window))
            
        except Exception as e:
            print(f"应用浅色主题失败: {e}")
            # 如果失败，使用系统默认调色板作为回退
            app.setPalette(app.style().standardPalette())
            self._override_main_window_sys_bg(app.palette().color(QPalette.ColorRole.Window))
    
    def _override_main_window_sys_bg(self, color):
        """覆写主窗口的sys_bg变量"""
        # 直接使用保存的主窗口引用
        if self.main_window and hasattr(self.main_window, 'sys_bg'):
            self.main_window.sys_bg = color
            print(f"sys_bg 覆写为: {color.getRgb()}")
    
    def get_current_theme(self):
        """获取当前主题"""
        return self.current_theme
    
    def get_actual_theme(self):
        """获取实际应用的主题（考虑auto模式）"""
        if self.current_theme == "auto":
            # 当主题是auto时，返回系统主题
            return self.system_theme
        return self.current_theme
    
    def update_system_theme(self, theme):
        """手动更新系统主题（用于测试或特殊情况）"""
        if theme in ["light", "dark"] and theme != self.system_theme:
            self.system_theme = theme
            # 如果当前主题是auto，则重新应用系统主题
            if self.current_theme == "auto":
                self._apply_system_theme()
                self.theme_changed.emit("auto")