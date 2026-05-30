"""
应用配置管理

提供统一的配置访问接口，集中管理所有应用配置
"""
from typing import Any, Optional
from .config_provider import config_provider


class AppConfig:
    """应用配置类
    
    集中管理所有应用配置，提供类型安全的访问方法
    """
    
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return config_provider.get(key, default)
    
    def get_all(self) -> dict:
        """获取所有配置"""
        return config_provider.get_all()
    
    # ========== 主题配置 ==========
    @property
    def theme(self) -> str:
        return self.get("theme", "auto")
    
    @property
    def background_image(self) -> str:
        return self.get("background_image", "")
    
    @property
    def start_random(self) -> bool:
        return self.get("start_random", False)
    
    # ========== 路径配置 ==========
    @property
    def start_path(self) -> str:
        import os
        return self.get("start_path", os.path.expanduser("~"))
    
    # ========== 显示配置 ==========
    @property
    def show_hidden_files(self) -> bool:
        return self.get("show_hidden_files", False)
    
    @property
    def show_all_sizes(self) -> bool:
        return self.get("show_all_sizes", False)
    
    @property
    def show_mtime(self) -> bool:
        return self.get("show_mtime", False)
    
    # ========== 字体配置 ==========
    @property
    def font_family(self) -> str:
        return self.get("font_family", "等线")
    
    @property
    def font_size(self) -> int:
        return self.get("font_size", 12)
    
    @property
    def status_font_size(self) -> int:
        return self.get("status_font_size", int(self.font_size * 0.7))
    
    @property
    def nav_tree_font_size(self) -> int:
        return self.get("nav_tree_font_size", self.font_size)
    
    @property
    def file_list_font_size(self) -> int:
        return self.get("file_list_font_size", 12)
    
    # ========== 图标配置 ==========
    @property
    def nav_tree_icon_size(self) -> float:
        return self.get("nav_tree_icon_size", self.font_size * 2.5)
    
    @property
    def file_list_icon_size(self) -> int:
        return self.get("file_list_icon_size", 40)
    
    @property
    def drive_icon_size(self) -> int:
        return self.get("drive_icon_size", 32)
    
    # ========== 透明度配置 ==========
    @property
    def nav_tree_bg_alpha(self) -> int:
        return self.get("nav_tree_bg_alpha", 128)
    
    @property
    def file_list_bg_alpha(self) -> int:
        return self.get("file_list_bg_alpha", 128)
    
    # ========== 日志配置 ==========
    @property
    def log_dir(self) -> str:
        return self.get("log_dir", "logs")
    
    @property
    def log_level(self) -> str:
        return self.get("log_level", "DEBUG").upper()
    
    @property
    def log_rotate_when(self) -> str:
        return self.get("log_rotate_when", "midnight")
    
    @property
    def log_rotate_interval(self) -> int:
        return self.get("log_rotate_interval", 1)
    
    @property
    def log_backup_count(self) -> int:
        return self.get("log_backup_count", 7)


# 全局配置实例
app_config = AppConfig()
