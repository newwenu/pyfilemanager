"""
主题感知组件支持

提供统一的主题管理接口，支持函数式和类继承两种方式
"""
from PySide6.QtWidgets import QWidget, QTreeWidget, QStatusBar
from PySide6.QtCore import QObject
from core import event_bus, app_config


def setup_theme_aware_widget(widget: QWidget, update_style_callback):
    """设置组件为主题感知
    
    函数式方式，不需要继承，直接为任意 QWidget 添加主题管理能力
    
    Args:
        widget: 要设置的组件
        update_style_callback: 样式更新回调函数，接收 (theme: str, sys_bg_rgb: tuple)
    
    示例:
        def update_my_widget_style(theme, sys_bg_rgb):
            r, g, b = sys_bg_rgb
            widget.setStyleSheet(f"background-color: rgba({r}, {g}, {b}, 128)")
        
        setup_theme_aware_widget(my_widget, update_my_widget_style)
    """
    def on_theme_changed(theme: str, sys_bg_rgb: tuple):
        update_style_callback(theme, sys_bg_rgb)
        widget.viewport().update() if hasattr(widget, 'viewport') else widget.update()
    
    # 订阅主题改变事件
    event_bus.theme_changed.connect(on_theme_changed)
    
    # 保存连接以便清理
    widget._theme_connection = on_theme_changed
    
    # 立即应用当前主题
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPalette
    sys_bg = QApplication.palette().color(QPalette.ColorRole.Window)
    r, g, b, _ = sys_bg.getRgb()
    
    # 尝试获取当前主题
    theme = "light"
    parent = widget.parent()
    while parent:
        if hasattr(parent, 'theme_manager') and parent.theme_manager:
            theme = parent.theme_manager.get_actual_theme()
            break
        parent = parent.parent()
    
    update_style_callback(theme, (r, g, b))


def setup_tree_widget_theme(widget: QTreeWidget, bg_alpha: int, icon_size: int, is_file_list: bool = False):
    """为树形控件设置主题感知
    
    Args:
        widget: QTreeWidget 实例
        bg_alpha: 背景透明度
        icon_size: 图标大小
        is_file_list: 是否是文件列表（影响item margins，与焦点样式过滤器保持一致）
    """
    def update_style(theme: str, sys_bg_rgb: tuple):
        r, g, b = sys_bg_rgb
        margin_style = "margin: 0.5px 0;" if is_file_list else ""
        widget.setStyleSheet(f"""
            QTreeWidget {{
                background-color: rgba({r}, {g}, {b}, {bg_alpha});
            }}
            QTreeWidget::item {{ 
                height: {icon_size}px;
                padding-left: 1px;
                {margin_style}
            }}
        """)
    
    setup_theme_aware_widget(widget, update_style)


def setup_statusbar_theme(widget: QStatusBar):
    """为状态栏设置主题感知"""
    def update_style(theme: str, sys_bg_rgb: tuple):
        r, g, b = sys_bg_rgb
        text_color = "220, 220, 220" if theme == "dark" else "0, 0, 0"
        widget.setStyleSheet(f"""
            QStatusBar {{
                background-color: rgba({r}, {g}, {b}, {app_config.nav_tree_bg_alpha});
                color: rgba({text_color}, 255);
                font-size: {app_config.status_font_size}pt;
            }}
        """)
    
    setup_theme_aware_widget(widget, update_style)


def setup_breadcrumb_theme(widget: QWidget):
    """为面包屑地址栏设置主题感知"""
    def update_style(theme: str, sys_bg_rgb: tuple):
        r, g, b = sys_bg_rgb
        widget.setStyleSheet(f"""
            BreadcrumbBar {{
                background-color: rgba({r}, {g}, {b}, 100);
                border-radius: 3px;
            }}
        """)
    
    setup_theme_aware_widget(widget, update_style)


def setup_searchbox_theme(widget: QWidget):
    """为搜索框设置主题感知"""
    def update_style(theme: str, sys_bg_rgb: tuple):
        r, g, b = sys_bg_rgb
        widget.setStyleSheet(f"""
            SearchBox {{
                background-color: rgba({r}, {g}, {b}, 120);
                border-radius: 4px;
                border: 1px solid rgba({r}, {g}, {b}, 150);
            }}
        """)
    
    setup_theme_aware_widget(widget, update_style)


def setup_more_options_button_theme(widget: QWidget):
    """为更多选项按钮设置主题感知"""
    def update_style(theme: str, sys_bg_rgb: tuple):
        r, g, b = sys_bg_rgb
        # 根据主题调整文字颜色
        text_color = "#eeeeee" if theme == "dark" else "#333333"
        hover_color = "#ffffff" if theme == "dark" else "#000000"
        widget.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba({r}, {g}, {b}, 100);
                border: none;
                border-radius: 3px;
                color: {text_color};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba({r}, {g}, {b}, 150);
                color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: rgba({r}, {g}, {b}, 200);
            }}
        """)
    
    setup_theme_aware_widget(widget, update_style)


# 向后兼容：保留类继承方式
class ThemeAwareMixin:
    """主题感知混入类（类继承方式）"""
    
    def __init_theme_aware__(self):
        """初始化主题感知（在子类 __init__ 中调用）"""
        def on_theme_changed(theme: str, sys_bg_rgb: tuple):
            self.update_theme_style(theme, sys_bg_rgb)
        
        event_bus.theme_changed.connect(on_theme_changed)
        self._theme_connection = on_theme_changed
        
        # 初始化时应用当前主题
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPalette
        
        sys_bg = QApplication.palette().color(QPalette.ColorRole.Window)
        r, g, b, _ = sys_bg.getRgb()
        
        theme = "light"
        parent = self.parent()
        while parent:
            if hasattr(parent, 'theme_manager') and parent.theme_manager:
                theme = parent.theme_manager.get_actual_theme()
                break
            parent = parent.parent()
        
        self.update_theme_style(theme, (r, g, b))
    
    def update_theme_style(self, theme: str, sys_bg_rgb: tuple):
        """更新主题样式（子类必须实现）"""
        raise NotImplementedError("子类必须实现 update_theme_style 方法")
