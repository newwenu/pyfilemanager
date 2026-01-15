"""
图标管理器模块 - 使用新的图标配置系统
负责图标的加载、缓存和管理
"""
import os
from typing import Dict
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtCore import Qt, QObject, Signal
from .icon_config_manager import IconConfigManager

class IconManager(QObject):
    """图标管理器 - 使用新的图标配置系统"""
    # 信号：图标缓存更新时发出
    icon_cache_updated = Signal()
    
    def __init__(self, config_manager: IconConfigManager = None, 
                 icon_size: int = 32, 
                 config_path: str = "userdata/file-icon-type/icon-config.json",
                 fallback_config_path: str = "userdata/file-icon-type/file-icon_type.json"):
        super().__init__()
        self.icon_size = icon_size
        
        # 初始化配置管理器
        self.config_manager = config_manager or IconConfigManager(config_path, fallback_config_path)
        
        # 连接配置管理器的信号
        self.config_manager.theme_changed.connect(self._on_theme_changed)
        
        # 图标缓存
        self.icon_cache: Dict[str, QIcon] = {}
        self.char_icon_cache: Dict[str, QIcon] = {}
        
        # 初始化图标缓存
        self._init_icon_cache()
    
    def _on_theme_changed(self, theme_name: str):
        """主题变更时清空缓存并重新初始化"""
        self.icon_cache.clear()
        self.char_icon_cache.clear()
        self._init_icon_cache()
        self.icon_cache_updated.emit()
    
    def _init_icon_cache(self):
        """初始化图标缓存"""
        # 预加载所有图标映射中的图标
        for mapping in self.config_manager.icon_mappings:
            icon_path = self.config_manager.get_icon_path(mapping.name)
            if icon_path and os.path.exists(icon_path):
                self._load_icon_from_file(mapping.name, icon_path)
        
        # 加载默认图标
        default_icon_path = self.config_manager.get_icon_path(self.config_manager.default_icon.name)
        if default_icon_path and os.path.exists(default_icon_path):
            self._load_icon_from_file(self.config_manager.default_icon.name, default_icon_path)
    
    def _load_icon_from_file(self, icon_name: str, icon_path: str):
        """从文件加载图标"""
        try:
            icon = QIcon(icon_path)
            if not icon.isNull():
                self.icon_cache[icon_name] = icon
                return True
        except Exception as e:
            print(f"加载图标失败 {icon_path}: {e}")
        return False
    
    def get_icon(self, file_path: str, file_properties: dict = None) -> QIcon:
        """获取文件对应的图标"""
        # 1. 获取图标名称
        icon_name = self.config_manager.get_icon_for_file(file_path, file_properties)
        
        # 2. 尝试从缓存获取图标
        if icon_name in self.icon_cache:
            return self.icon_cache[icon_name]
        
        # 3. 尝试从文件系统加载图标
        icon_path = self.config_manager.get_icon_path(icon_name)
        if icon_path and os.path.exists(icon_path):
            if self._load_icon_from_file(icon_name, icon_path):
                return self.icon_cache[icon_name]
        
        # 4. 使用字符图标作为回退
        return self.get_char_icon(icon_name)
    
    def get_char_icon(self, icon_name: str) -> QIcon:
        """获取字符图标"""
        if icon_name in self.char_icon_cache:
            return self.char_icon_cache[icon_name]
        
        # 获取字符回退图标
        char_fallback = self.config_manager.get_char_fallback(icon_name)
        if not char_fallback:
            char_fallback = "📄"  # 默认字符图标
        
        # 创建字符图标
        pixmap = QPixmap(self.icon_size, self.icon_size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setPen(Qt.black)
        font = painter.font()
        font.setPixelSize(int(self.icon_size * 0.7))
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, char_fallback)
        painter.end()
        
        icon = QIcon(pixmap)
        self.char_icon_cache[icon_name] = icon
        return icon
    
    def get_icon_by_name(self, icon_name: str) -> QIcon:
        """根据图标名称获取图标"""
        # 尝试从缓存获取
        if icon_name in self.icon_cache:
            return self.icon_cache[icon_name]
        
        # 尝试从文件系统加载
        icon_path = self.config_manager.get_icon_path(icon_name)
        if icon_path and os.path.exists(icon_path):
            if self._load_icon_from_file(icon_name, icon_path):
                return self.icon_cache[icon_name]
        
        # 使用字符图标
        return self.get_char_icon(icon_name)
    
    def set_icon_size(self, size: int):
        """设置图标大小"""
        if size != self.icon_size:
            self.icon_size = size
            # 清空字符图标缓存，因为大小变了
            self.char_icon_cache.clear()
            self.icon_cache_updated.emit()
    
    def refresh_cache(self):
        """刷新图标缓存"""
        self.icon_cache.clear()
        self.char_icon_cache.clear()
        self._init_icon_cache()
        self.icon_cache_updated.emit()
    
    def add_custom_icon(self, icon_name: str, icon_path: str) -> bool:
        """添加自定义图标"""
        if os.path.exists(icon_path):
            return self._load_icon_from_file(icon_name, icon_path)
        return False
    
    def get_available_themes(self):
        """获取所有可用主题"""
        return self.config_manager.get_available_themes()
    
    def set_active_theme(self, theme_name: str):
        """设置当前活动主题"""
        self.config_manager.set_active_theme(theme_name)