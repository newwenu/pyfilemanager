"""
图标管理器模块 - 使用新的图标配置系统
负责图标的加载、缓存和管理
"""
import os
from utils.logging_config import get_logger
from typing import Dict
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtCore import Qt, QObject, Signal
from .icon_config_manager import IconConfigManager
from .extension_manager import ExtensionManager
from .init_extensions import initialize_extensions

# 获取日志记录器
logger = get_logger(__name__)

class IconManager(QObject):
    """图标管理器 - 使用新的图标配置系统"""
    # 信号：图标缓存更新时发出
    icon_cache_updated = Signal()
    
    def __init__(self, config_manager: IconConfigManager = None, 
                 icon_size: int = 32, 
                 config_path: str = "userdata/file-icon-type/icon-config.json",
                 fallback_config_path: str = "userdata/file-icon-type/file-icon_type.json",
                 extension_config_path: str = "userdata/file-icon-type/extensions_collection.json"):
        super().__init__()
        self.icon_size = icon_size
        
        # 初始化配置管理器
        self.config_manager = config_manager or IconConfigManager(config_path, fallback_config_path)
        
        # 初始化扩展名管理器
        self.extension_manager = ExtensionManager(extension_config_path)
        
        # 连接配置管理器的信号
        self.config_manager.theme_changed.connect(self._on_theme_changed)
        
        # 图标缓存
        self.icon_cache: Dict[str, QIcon] = {}
        self.char_icon_cache: Dict[str, QIcon] = {}
        self.system_icon_cache: Dict[str, QIcon] = {}  # 系统图标缓存
        
        # 初始化图标缓存
        self._init_icon_cache()
        
        # 初始化扩展名集合（如果需要）
        # self._init_extensions_collection()

    def _init_extensions_collection(self):
        """初始化扩展名集合"""
        initialize_extensions()

    def _on_theme_changed(self, theme_name: str):
        """主题变更时清空缓存并重新初始化"""
        self.icon_cache.clear()
        self.char_icon_cache.clear()
        self.system_icon_cache.clear()  # 清空系统图标缓存
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
            logger.error(f"加载图标失败 {icon_path}: {e}")
        return False
    
    def get_icon(self, file_path: str, file_properties: dict = None) -> QIcon:
        """获取文件对应的图标"""
        # 1. 获取图标名称
        icon_name = self.config_manager.get_icon_for_file(file_path, file_properties)
        print(f"获取图标名称: {icon_name}")
        # # 2. 检查是否是默认图标，如果是，尝试从扩展名集合获取系统图标
        # if icon_name == self.config_manager.default_icon.name:
            # # 开始计时
            # import time
            # start_time = time.perf_counter()
            
            # # 获取文件扩展名
            # from pathlib import Path
            # file_ext = Path(file_path).suffix.lower()
            # logger.info(f"获取文件扩展名: {file_ext}")
            # # 检查扩展名是否在扩展名集合中
            # is_registered = self.extension_manager.is_extension_registered(file_ext)
            # logger.info(f"扩展名 {file_ext} 是否在扩展名集合中: {is_registered}")
            # if is_registered:
            #     # 尝试获取系统图标
            #     system_icon = self._get_system_icon(file_ext, file_path)
            #     if system_icon:
            #         logger.info(f"成功获取系统图标: {file_ext}")
            #         # 计算并记录执行时间
            #         end_time = time.perf_counter()
            #         execution_time = (end_time - start_time) * 1000  # 转换为毫秒
            #         logger.info(f"92-105行代码执行时间: {execution_time:.4f} 毫秒")
            #         return system_icon
            
            # # 即使没有获取到系统图标，也计算执行时间
            # end_time = time.perf_counter()
            # execution_time = (end_time - start_time) * 1000  # 转换为毫秒
            # logger.info(f"92-105行代码执行时间: {execution_time:.4f} 毫秒")
            # print(f"是默认图标: {icon_name}")
        # 3. 尝试从缓存获取图标
        if icon_name in self.icon_cache:
            return self.icon_cache[icon_name]
        
        # 0-. 尝试从文件系统加载图标
        icon_path = self.config_manager.get_icon_path(icon_name)
        if icon_path and os.path.exists(icon_path):
            if self._load_icon_from_file(icon_name, icon_path):
                return self.icon_cache[icon_name]
        

        # 0-5. 使用字符图标作为回退
        logger.info(f"使用字符图标作为回退: {icon_name}")
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
    
    def _get_system_icon(self, file_ext: str, file_path: str) -> QIcon:
        """获取系统图标"""
        # 检查系统图标缓存
        cache_key = f"{file_ext}:{file_path}"
        if cache_key in self.system_icon_cache:
            return self.system_icon_cache[cache_key]
        
        try:
            # 导入ink_icon模块
            # from .ink_icon import get_file_icon
            
            # 尝试获取系统图标，传入图标大小
            # pixmap = get_file_icon(file_path, self.icon_size)
            # if pixmap and not pixmap.isNull():
            #     # 将QPixmap转换为QIcon
            #     icon = QIcon(pixmap)
            #     # 添加到缓存
            #     self.system_icon_cache[cache_key] = icon
            #     logger.info(f"成功获取系统图标: {file_ext}")
            #     return icon
            pass
        except ImportError:
            logger.error("无法导入ink_icon模块")
        except Exception as e:
            logger.error(f"获取系统图标失败: {e}")
        
        return None
    
    def refresh_extensions(self):
        """刷新扩展名集合"""
        try:
            # 使用扩展名管理器刷新扩展名
            stats = self.extension_manager.scan_and_save_extensions()
            success = stats["total_saved"] > 0
            
            if success:
                logger.info(f"扩展名集合刷新成功，共 {stats['total_saved']} 个扩展名")
                # 清空系统图标缓存，因为扩展名集合可能已更新
                self.system_icon_cache.clear()
            else:
                logger.warning("扩展名集合刷新失败")
                
            return success
        except Exception as e:
            logger.error(f"刷新扩展名集合时出错: {e}")
            return False
    
    def get_extensions_count(self):
        """获取扩展名集合中的扩展名数量"""
        try:
            return self.extension_manager.get_extensions_count()
        except Exception as e:
            logger.error(f"获取扩展名数量时出错: {e}")
            return 0