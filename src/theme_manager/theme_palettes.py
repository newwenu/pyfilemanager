"""
主题调色板定义模块
定义深色和浅色主题的调色板配置
"""
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


class ThemePalettes:
    """主题调色板类"""
    
    # 深色主题颜色定义
    DARK_COLORS = {
        # 窗口相关
        "window": QColor(43, 43, 43),
        "window_text": QColor(220, 220, 220),
        "base": QColor(30, 30, 30),
        "alternate_base": QColor(43, 43, 43),
        
        # 工具提示
        "tooltip_base": QColor(50, 50, 50),
        "tooltip_text": QColor(220, 220, 220),
        
        # 文字
        "text": QColor(220, 220, 220),
        "button_text": QColor(220, 220, 220),
        "bright_text": QColor(255, 255, 255),
        
        # 按钮
        "button": QColor(60, 60, 60),
        "button_highlight": QColor(70, 70, 70),
        
        # 高亮/选中
        "highlight": QColor(0, 120, 215),
        "highlighted_text": QColor(255, 255, 255),
        
        # 链接
        "link": QColor(100, 180, 255),
        "link_visited": QColor(150, 120, 255),
        
        # 边框
        "mid": QColor(80, 80, 80),
        "midlight": QColor(90, 90, 90),
        "dark": QColor(35, 35, 35),
        "light": QColor(70, 70, 70),
        
        # 阴影
        "shadow": QColor(20, 20, 20),
        
        # 悬浮效果（半透明）
        "hover": QColor(100, 100, 100, 80),
        "hover_light": QColor(120, 120, 120, 60),
    }
    
    # 浅色主题颜色定义
    LIGHT_COLORS = {
        # 窗口相关
        "window": QColor(240, 240, 240),
        "window_text": QColor(0, 0, 0),
        "base": QColor(255, 255, 255),
        "alternate_base": QColor(233, 233, 233),
        
        # 工具提示
        "tooltip_base": QColor(255, 255, 220),
        "tooltip_text": QColor(0, 0, 0),
        
        # 文字
        "text": QColor(0, 0, 0),
        "button_text": QColor(0, 0, 0),
        "bright_text": QColor(255, 255, 255),
        
        # 按钮
        "button": QColor(225, 225, 225),
        "button_highlight": QColor(240, 240, 240),
        
        # 高亮/选中
        "highlight": QColor(0, 120, 215),
        "highlighted_text": QColor(255, 255, 255),
        
        # 链接
        "link": QColor(0, 0, 255),
        "link_visited": QColor(128, 0, 128),
        
        # 边框
        "mid": QColor(160, 160, 160),
        "midlight": QColor(200, 200, 200),
        "dark": QColor(160, 160, 160),
        "light": QColor(255, 255, 255),
        
        # 阴影
        "shadow": QColor(100, 100, 100),
        
        # 悬浮效果（半透明）
        "hover": QColor(200, 200, 200, 80),
        "hover_light": QColor(220, 220, 220, 60),
    }
    
    @classmethod
    def create_palette(cls, colors: dict) -> QPalette:
        """
        从颜色字典创建调色板
        
        Args:
            colors: 颜色字典
            
        Returns:
            QPalette 实例
        """
        palette = QPalette()
        
        # 窗口相关
        palette.setColor(QPalette.ColorRole.Window, colors["window"])
        palette.setColor(QPalette.ColorRole.WindowText, colors["window_text"])
        palette.setColor(QPalette.ColorRole.Base, colors["base"])
        palette.setColor(QPalette.ColorRole.AlternateBase, colors["alternate_base"])
        
        # 工具提示
        palette.setColor(QPalette.ColorRole.ToolTipBase, colors["tooltip_base"])
        palette.setColor(QPalette.ColorRole.ToolTipText, colors["tooltip_text"])
        
        # 文字
        palette.setColor(QPalette.ColorRole.Text, colors["text"])
        palette.setColor(QPalette.ColorRole.ButtonText, colors["button_text"])
        palette.setColor(QPalette.ColorRole.BrightText, colors["bright_text"])
        
        # 按钮
        palette.setColor(QPalette.ColorRole.Button, colors["button"])
        
        # 高亮
        palette.setColor(QPalette.ColorRole.Highlight, colors["highlight"])
        palette.setColor(QPalette.ColorRole.HighlightedText, colors["highlighted_text"])
        
        # 链接
        palette.setColor(QPalette.ColorRole.Link, colors["link"])
        palette.setColor(QPalette.ColorRole.LinkVisited, colors["link_visited"])
        
        # 边框
        palette.setColor(QPalette.ColorRole.Mid, colors["mid"])
        palette.setColor(QPalette.ColorRole.Midlight, colors["midlight"])
        palette.setColor(QPalette.ColorRole.Dark, colors["dark"])
        palette.setColor(QPalette.ColorRole.Light, colors["light"])
        
        # 阴影
        palette.setColor(QPalette.ColorRole.Shadow, colors["shadow"])
        
        # 禁用状态的颜色
        disabled_color = colors["window_text"]
        disabled_color.setAlpha(128)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_color)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_color)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_color)
        
        return palette
    
    @classmethod
    def get_dark_palette(cls) -> QPalette:
        """获取深色主题调色板"""
        return cls.create_palette(cls.DARK_COLORS)
    
    @classmethod
    def get_light_palette(cls) -> QPalette:
        """获取浅色主题调色板"""
        return cls.create_palette(cls.LIGHT_COLORS)
    
    @classmethod
    def get_colors(cls, theme: str) -> dict:
        """
        获取主题颜色字典
        
        Args:
            theme: 'dark' 或 'light'
            
        Returns:
            颜色字典
        """
        if theme == "dark":
            return cls.DARK_COLORS
        return cls.LIGHT_COLORS
