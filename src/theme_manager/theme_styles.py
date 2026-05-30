"""
主题样式表定义模块
为文件管理器各组件定义 QSS 样式
"""
from .theme_palettes import ThemePalettes


class ThemeStyles:
    """主题样式类"""
    
    @classmethod
    def get_stylesheet(cls, theme: str) -> str:
        """
        获取完整样式表
        
        Args:
            theme: 'dark' 或 'light'
            
        Returns:
            QSS 样式表字符串
        """
        colors = ThemePalettes.get_colors(theme)
        
        # 获取颜色值（十六进制）
        c = {}
        for k, v in colors.items():
            if v.alpha() < 255:
                # 半透明颜色使用 rgba 格式
                c[k] = f"rgba({v.red()}, {v.green()}, {v.blue()}, {v.alpha()})"
            else:
                c[k] = v.name()
        
        return f"""
        /* ==================== 分割器 ==================== */
        QSplitter::handle {{
            background-color: {c['mid']};
        }}
        
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        
        QSplitter::handle:hover {{
            background-color: {c['highlight']};
        }}
        
        /* ==================== 标签页 ==================== */
        QTabWidget::pane {{
            background-color: {c['window']};
            border: 1px solid {c['mid']};
            border-radius: 0 0 4px 4px;
            top: -1px;
            padding: 8px;
        }}
        
        QTabBar::tab {{
            background-color: {c['alternate_base']};
            color: {c['text']};
            border: 1px solid {c['mid']};
            border-bottom: 1px solid {c['mid']};
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 6px 14px;
            margin-right: 2px;
            min-width: 60px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {c['window']};
            border-bottom: 1px solid {c['window']};
            color: {c['highlight']};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {c['button_highlight']};
        }}
        
        QTabBar::tab:!selected {{
            margin-top: 2px;
        }}
        """
    
    @classmethod
    def get_file_list_style(cls, theme: str) -> str:
        """
        获取文件列表专用样式（用于动态更新）
        
        Args:
            theme: 'dark' 或 'light'
            
        Returns:
            QSS 样式字符串
        """
        colors = ThemePalettes.get_colors(theme)
        c = {k: v.name() for k, v in colors.items()}
        
        return f"""
        QListWidget {{
            background-color: {c['base']};
            color: {c['text']};
            border: 1px solid {c['mid']};
            outline: none;
        }}
        
        QListWidget::item {{
            padding: 8px;
            border-radius: 4px;
            margin: 2px;
        }}
        
        QListWidget::item:selected {{
            background-color: {c['highlight']};
            color: {c['highlighted_text']};
        }}
        
        QListWidget::item:hover {{
            background-color: {c['alternate_base']};
        }}
        """
    
    @classmethod
    def get_breadcrumb_style(cls, theme: str) -> str:
        """
        获取面包屑地址栏样式
        
        Args:
            theme: 'dark' 或 'light'
            
        Returns:
            QSS 样式字符串
        """
        colors = ThemePalettes.get_colors(theme)
        c = {}
        for k, v in colors.items():
            if v.alpha() < 255:
                c[k] = f"rgba({v.red()}, {v.green()}, {v.blue()}, {v.alpha()})"
            else:
                c[k] = v.name()
        
        return f"""
        BreadcrumbBar {{
            background-color: {c['button']};
            border-radius: 3px;
        }}
        
        BreadcrumbBar QLabel {{
            color: {c['text']};
            padding: 0px 2px;
            font-size: 12px;
        }}
        
        BreadcrumbBar QLabel:hover {{
            color: {c['bright_text']};
            background-color: {c['hover']};
            border-radius: 2px;
        }}
        
        BreadcrumbBar QPushButton {{
            background-color: transparent;
            border: none;
            color: {c['text']};
            padding: 0px 4px;
            font-size: 12px;
        }}
        
        BreadcrumbBar QPushButton:hover {{
            color: {c['bright_text']};
            background-color: {c['hover']};
            border-radius: 2px;
        }}
        
        BreadcrumbBar QLineEdit {{
            background-color: {c['base']};
            border: 1px solid {c['highlight']};
            border-radius: 2px;
            color: {c['text']};
            padding: 1px 4px;
            font-size: 12px;
        }}
        """
    
    @classmethod
    def get_search_box_style(cls, theme: str) -> str:
        """
        获取搜索框样式
        
        Args:
            theme: 'dark' 或 'light'
            
        Returns:
            QSS 样式字符串
        """
        colors = ThemePalettes.get_colors(theme)
        c = {}
        for k, v in colors.items():
            if v.alpha() < 255:
                c[k] = f"rgba({v.red()}, {v.green()}, {v.blue()}, {v.alpha()})"
            else:
                c[k] = v.name()
        
        return f"""
        SearchBox {{
            background-color: {c['button']};
            border-radius: 4px;
            border: 1px solid {c['mid']};
        }}
        
        SearchBox QLineEdit {{
            background-color: transparent;
            border: none;
            color: {c['text']};
            font-size: 12px;
            padding: 2px;
        }}
        
        SearchBox QPushButton {{
            background-color: {c['alternate_base']};
            border: none;
            border-radius: 2px;
            color: {c['text']};
            font-size: 10px;
        }}
        
        SearchBox QPushButton:hover {{
            background-color: {c['hover']};
            color: {c['bright_text']};
        }}
        """
    
    @classmethod
    def get_more_options_button_style(cls, theme: str) -> str:
        """
        获取更多选项按钮样式
        
        Args:
            theme: 'dark' 或 'light'
            
        Returns:
            QSS 样式字符串
        """
        colors = ThemePalettes.get_colors(theme)
        c = {}
        for k, v in colors.items():
            if v.alpha() < 255:
                c[k] = f"rgba({v.red()}, {v.green()}, {v.blue()}, {v.alpha()})"
            else:
                c[k] = v.name()
        
        return f"""
        MoreOptionsButton {{
            background-color: {c['button']};
            border: none;
            border-radius: 3px;
            color: {c['text']};
            font-size: 16px;
            font-weight: bold;
        }}
        
        MoreOptionsButton:hover {{
            background-color: {c['button_highlight']};
            color: {c['bright_text']};
        }}
        
        MoreOptionsButton:pressed {{
            background-color: {c['highlight']};
        }}
        """
    
    @classmethod
    def get_menu_style(cls, theme: str) -> str:
        """
        获取菜单样式（用于更多选项按钮的菜单）
        
        Args:
            theme: 'dark' 或 'light'
            
        Returns:
            QSS 样式字符串
        """
        colors = ThemePalettes.get_colors(theme)
        c = {}
        for k, v in colors.items():
            if v.alpha() < 255:
                c[k] = f"rgba({v.red()}, {v.green()}, {v.blue()}, {v.alpha()})"
            else:
                c[k] = v.name()
        
        return f"""
        QMenu {{
            background-color: {c['window']};
            border: 1px solid {c['mid']};
            border-radius: 4px;
            padding: 4px;
        }}
        
        QMenu::item {{
            color: {c['text']};
            padding: 6px 20px;
            font-size: 12px;
            border-radius: 2px;
        }}
        
        QMenu::item:selected {{
            background-color: {c['highlight']};
            color: {c['highlighted_text']};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {c['mid']};
            margin: 4px 8px;
        }}
        """
