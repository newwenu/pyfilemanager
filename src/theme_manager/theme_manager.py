"""
主题管理器 - 处理应用程序主题设置
支持深色、浅色和自动（跟随系统）主题
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import Qt




class ThemeManager(QObject):
    """主题管理器类
    
    主题改变通过事件总线通知，实现模块间解耦
    """
    
    # 主题改变信号（传递主题名称和系统背景色RGB）
    theme_changed = Signal(str, tuple)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_theme = None
        self.main_window = parent  # 保存主窗口引用
        self._system_theme_connected = False  # 跟踪信号连接状态
        
    def apply_theme(self, theme_name: str):
        """
        应用主题
        
        Args:
            theme_name: 'dark', 'light', 或 'auto'
        """
        if theme_name == self.current_theme and theme_name != 'auto':
            return
            
        self.current_theme = theme_name
        app = QApplication.instance()
        
        if not app:
            return
            
        try:
            # 确定实际应用的主题
            actual_theme = self._resolve_theme(theme_name)
            
            # 设置 Qt 原生颜色方案（影响系统背景色）
            self._apply_color_scheme(app, actual_theme)
            
            # 设置系统主题监听（如果是 auto 模式）
            if theme_name == "auto":
                self._setup_system_theme_listener()
            else:
                self._remove_system_theme_listener()
            
            # 获取系统背景色并发送主题改变事件
            from PySide6.QtGui import QPalette
            sys_bg = app.palette().color(QPalette.ColorRole.Window)
            r, g, b, _ = sys_bg.getRgb()
            
            # 发送主题改变信号（同时通过直接信号和事件总线）
            # 传递主题名称和系统背景色RGB，让各组件自行处理样式
            self.theme_changed.emit(actual_theme, (r, g, b))
            from core import event_bus
            event_bus.theme_changed.emit(actual_theme, (r, g, b))
            
        except Exception as e:
            print(f"应用主题失败: {e}")
    
    def _resolve_theme(self, theme_name: str) -> str:
        """
        解析主题名称
        
        Args:
            theme_name: 'dark', 'light', 或 'auto'
            
        Returns:
            实际的主题名称 'dark' 或 'light'
        """
        if theme_name == "auto":
            return self._get_system_theme()
        return theme_name
    
    def _get_system_theme(self) -> str:
        """
        获取当前系统主题
        
        Returns:
            'dark' 或 'light'
        """
        app = QApplication.instance()
        if not app:
            return "light"
        app.styleHints().unsetColorScheme() # 先清理应用的主题
        # 再使用 Qt 6 的 styleHints 获取系统颜色方案
        color_scheme = app.styleHints().colorScheme()
        # print("目前获取的主题",color_scheme)
        if color_scheme == Qt.ColorScheme.Dark:
            return "dark"
        elif color_scheme == Qt.ColorScheme.Light:
            return "light"
        else:
            # Unknown 或未定义，使用浅色作为默认
            return "light"
    
    def _apply_color_scheme(self, app, theme):
        hints = app.styleHints()
        if self.current_theme == "auto":
            # Auto模式：恢复跟随系统，这样才能持续读到系统的主题变化
            hints.unsetColorScheme()
        else:
            # 固定主题：才需要覆盖系统设置，让原生控件匹配我们的主题
            if theme == "dark":
                hints.setColorScheme(Qt.ColorScheme.Dark)
            else:
                hints.setColorScheme(Qt.ColorScheme.Light)
    
    def _setup_system_theme_listener(self):
        """设置系统主题变化监听"""
        app = QApplication.instance()
        if not app:
            return
        
        # 如果已经连接，先断开
        if self._system_theme_connected:
            self._remove_system_theme_listener()
        
        # 监听颜色方案变化信号
        try:
            app.styleHints().colorSchemeChanged.connect(self._on_system_theme_changed)
            self._system_theme_connected = True
        except Exception as e:
            print(f"设置系统主题监听失败: {e}")
    
    def _remove_system_theme_listener(self):
        """移除系统主题变化监听"""
        if not self._system_theme_connected:
            return
        
        app = QApplication.instance()
        if not app:
            return
        
        try:
            app.styleHints().colorSchemeChanged.disconnect(self._on_system_theme_changed)
            self._system_theme_connected = False
        except Exception:
            # 可能之前没有连接，忽略错误
            self._system_theme_connected = False
    
    @Slot(Qt.ColorScheme)
    def _on_system_theme_changed(self, color_scheme: Qt.ColorScheme):
        """
        系统主题变化回调
        
        Args:
            color_scheme: 新的颜色方案
        """
        if self.current_theme != "auto":
            return
        
        # 重新应用主题
        self.apply_theme("auto")
    
    def refresh_theme(self):
        """刷新当前主题（用于外部调用）"""
        if self.current_theme:
            self.apply_theme(self.current_theme)
    
    def get_current_theme(self) -> str:
        """
        获取当前主题
        
        Returns:
            当前主题名称 'dark', 'light', 或 'auto'
        """
        return self.current_theme
    
    def get_actual_theme(self) -> str:
        """
        获取实际应用的主题（解析 auto 后的主题）
        
        Returns:
            实际主题名称 'dark' 或 'light'
        """
        return self._resolve_theme(self.current_theme) if self.current_theme else "light"
    
    def cleanup(self):
        """清理资源"""
        self._remove_system_theme_listener()
