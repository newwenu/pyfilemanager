"""
主题管理器 - 处理应用程序主题设置
使用PySide6原生接口设置主题
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import Qt


class ThemeManager(QObject):
    """主题管理器类"""
    
    # 主题改变信号
    theme_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_theme = None
        self.main_window = parent  # 保存主窗口引用
        
    def apply_theme(self, theme_name):
        """应用主题 - 使用QApplication.styleHints().setColorScheme()"""
        if theme_name == self.current_theme:
            return
            
        self.current_theme = theme_name
        app = QApplication.instance()
        
        if not app:
            return
            
        try:
            if theme_name == "dark":
                # 使用PySide6原生接口设置深色主题
                app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
            elif theme_name == "light":
                # 使用PySide6原生接口设置浅色主题
                app.styleHints().setColorScheme(Qt.ColorScheme.Light)
            else:
                # 对于auto或其他情况，使用系统默认主题
                pass
                
            # 获取当前调色板颜色并更新主窗口
            current_palette = app.palette()
            # self._override_main_window_sys_bg(current_palette.color(current_palette.ColorRole.Window))
            
            # 发送主题改变信号
            self.theme_changed.emit(theme_name)
            
        except Exception as e:
            print(f"应用主题失败: {e}")
    
    def _override_main_window_sys_bg(self, color):
        """覆写主窗口的sys_bg变量"""
        return
        if self.main_window and hasattr(self.main_window, 'sys_bg'):
            self.main_window.sys_bg = color
            print(f"主题色已更新: {color.getRgb()}")
    
    def get_current_theme(self):
        """获取当前主题"""
        return self.current_theme