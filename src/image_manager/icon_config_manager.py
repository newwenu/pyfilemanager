"""
图标配置管理器模块
负责管理图标主题、图标映射规则和图标加载
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from PySide6.QtGui import QIcon
from PySide6.QtCore import QObject, Signal

@dataclass
class MatchRule:
    """图标匹配规则"""
    type: str  # "extension", "filename", "file_property", "content"
    patterns: List[str]
    priority: int = 10
    property: Optional[str] = None  # for file_property type
    value: Optional[str] = None  # for file_property type
    case_sensitive: bool = False  # 是否区分大小写

@dataclass
class IconMapping:
    """图标映射配置"""
    name: str
    display_name: str
    icon_file: str
    char_fallback: str
    match_rules: List[MatchRule] = field(default_factory=list)

@dataclass
class IconTheme:
    """图标主题配置"""
    name: str
    display_name: str
    base_path: str
    fallback_theme: Optional[str] = None

class IconConfigManager(QObject):
    """图标配置管理器"""
    # 信号：主题变更时发出
    theme_changed = Signal(str)
    
    def __init__(self, config_path: str = "userdata/file-icon-type/icon-config.json", 
                 fallback_config_path: str = "userdata/file-icon-type/file-icon_type.json"):
        super().__init__()
        self.config_path = config_path
        self.fallback_config_path = fallback_config_path
        self.config = self._load_config()
        self.active_theme = self.config.get("active_theme", "default")
        
        # 初始化主题和图标映射
        self._init_themes()
        self._init_icon_mappings()
        
        # 构建快速查找表
        # self._build_lookup_tables()
    
    def _init_themes(self):
        """初始化图标主题"""
        themes_config = self.config.get("icon_themes", {})
        
        # 如果没有主题配置，创建默认主题
        if not themes_config:
            themes_config = {
                "default": {
                    "name": "默认主题",
                    "base_path": "media",
                    "fallback_theme": None
                }
            }
            self.config["icon_themes"] = themes_config
        
        self.icon_themes = {
            name: IconTheme(**theme) 
            for name, theme in themes_config.items()
        }
    
    def _init_icon_mappings(self):
        """初始化图标映射"""
        mappings_config = self.config.get("icon_mappings", [])
        
        # 如果没有图标映射配置，尝试从旧配置转换
        if not mappings_config and os.path.exists(self.fallback_config_path):
            mappings_config = self._convert_legacy_config()
        
        # 确保有默认图标
        default_icon_config = self.config.get("default_icon", {
            "name": "default",
            "display_name": "默认文件",
            "icon_file": "file.png",
            "char_fallback": "📄"
        })
        
        # 将字典配置转换为MatchRule对象
        processed_mappings = []
        for mapping in mappings_config:
            # 处理匹配规则
            match_rules = []
            for rule in mapping.get("match_rules", []):
                if isinstance(rule, dict):
                    # 确保必需的patterns字段存在
                    if "patterns" not in rule:
                        rule["patterns"] = []
                    match_rules.append(MatchRule(**rule))
                else:
                    match_rules.append(rule)
            
            # 创建IconMapping对象
            mapping_data = {
                "name": mapping.get("name"),
                "display_name": mapping.get("display_name"),
                "icon_file": mapping.get("icon_file"),
                "char_fallback": mapping.get("char_fallback"),
                "match_rules": match_rules
            }
            processed_mappings.append(IconMapping(**mapping_data))
        
        self.icon_mappings = processed_mappings
        self.default_icon = IconMapping(**default_icon_config)
    
    def _convert_legacy_config(self) -> List[Dict[str, Any]]:
        """从旧配置转换为新格式"""
        try:
            with open(self.fallback_config_path, "r", encoding="utf-8") as f:
                legacy_config = json.load(f)
            
            file_type_mapping = legacy_config.get("file_type_mapping", {})
            mappings = []
            
            for file_type, extensions in file_type_mapping.items():
                if not extensions:  # 跳过空扩展名列表
                    continue
                
                mapping = {
                    "name": file_type,
                    "display_name": file_type,
                    "icon_file": f"{file_type}.png",
                    "char_fallback": self._get_default_char_for_type(file_type),
                    "match_rules": [
                        {
                            "type": "extension",
                            "patterns": extensions,
                            "priority": 10
                        }
                    ]
                }
                mappings.append(mapping)
            
            return mappings
        except Exception as e:
            print(f"转换旧配置失败: {e}")
            return []
    
    def _get_default_char_for_type(self, file_type: str) -> str:
        """获取文件类型对应的默认字符图标"""
        char_map = {
            'folder': '📂',
            'text': '📄',
            'image': '🖼️',
            'video': '🎥',
            'music': '🎵',
            'pdf': '📑',
            'archive': '📦',
            'exe': '🚀',
            'code': '🛠️',
            'hardware': '💾',
            'document': '📄',
            'spreadsheet': '📊',
            'font': '🔤',
            'database': '🗄️', 
            'shortcut': '🔗',
            'config': '⚙️',
            'defaulticon': '🚀'  # 特殊处理默认图标
        }
        return char_map.get(file_type, '📄')
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果新配置文件不存在，创建默认配置
            return self._create_default_config()
    
    def _create_default_config(self) -> dict:
        """创建默认配置"""
        default_config = {
            "icon_themes": {
                "default": {
                    "name": "默认主题",
                    "base_path": "media",
                    "fallback_theme": None
                }
            },
            "active_theme": "default",
            "icon_mappings": [],
            "default_icon": {
                "name": "default",
                "display_name": "默认文件",
                "icon_file": "file.png",
                "char_fallback": "📄"
            }
        }
        
        # 创建配置目录
        config_dir = os.path.dirname(self.config_path)
        Path(config_dir).mkdir(parents=True, exist_ok=True)
        
        # 保存默认配置
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"创建默认配置文件失败: {e}")
        
        return default_config
    
    # def _build_lookup_tables(self):
    #     """构建快速查找表"""
    #     self.ext_to_icon = {}
    #     self.filename_to_icon = {}
    #     self.property_to_icon = {}  # 文件属性到图标的映射
        
    #     for mapping in self.icon_mappings:
    #         for rule in mapping.match_rules:
    #             if rule.type == "extension":
    #                 for ext in rule.patterns:
    #                     if not ext:  # 跳过空扩展名
    #                         continue
    #                     ext_key = ext.lower() if not rule.case_sensitive else ext
    #                     if ext_key not in self.ext_to_icon or rule.priority > self.ext_to_icon[ext_key][1]:
    #                         self.ext_to_icon[ext_key] = (mapping.name, rule.priority)
                
    #             elif rule.type == "filename":
    #                 for pattern in rule.patterns:
    #                     if not pattern:  # 跳过空模式
    #                         continue
    #                     pattern_key = pattern.lower() if not rule.case_sensitive else pattern
    #                     if pattern_key not in self.filename_to_icon or rule.priority > self.filename_to_icon[pattern_key][1]:
    #                         self.filename_to_icon[pattern_key] = (mapping.name, rule.priority)
                
    #             elif rule.type == "file_property":
    #                 if rule.property:
    #                     prop_key = (rule.property.lower(), str(rule.value).lower()) if not rule.case_sensitive else (rule.property, str(rule.value))
    #                     if prop_key not in self.property_to_icon or rule.priority > self.property_to_icon[prop_key][1]:
    #                         self.property_to_icon[prop_key] = (mapping.name, rule.priority)
    
    # def get_icon_for_file(self, file_path: str, file_properties: dict = None) -> str:
    #     """根据文件路径获取图标名称"""
    #     file_path = Path(file_path)
    #     ext = file_path.suffix
    #     filename = file_path.stem
        
    #     # 1. 尝试通过扩展名匹配
    #     if ext:
    #         ext_key = ext.lower()
    #         if ext_key in self.ext_to_icon:
    #             return self.ext_to_icon[ext_key][0]
        
    #     # # 2. 尝试通过文件名匹配（支持正则表达式）
    #     # for mapping in self.icon_mappings:
    #     #     for rule in mapping.match_rules:
    #     #         if rule.type == "filename":
    #     #             for pattern in rule.patterns:
    #     #                 try:
    #     #                     # 尝试作为正则表达式匹配
    #     #                     if re.search(pattern, filename, re.IGNORECASE if not rule.case_sensitive else 0):
    #     #                         return mapping.name
    #     #                 except re.error:
    #     #                     # 如果不是有效的正则表达式，尝试精确匹配
    #     #                     pattern_key = pattern.lower() if not rule.case_sensitive else pattern
    #     #                     filename_key = filename.lower() if not rule.case_sensitive else filename
    #     #                     if pattern_key == filename_key:
    #     #                         return mapping.name
        
    #     # 4. 返回默认图标
    #     return self.default_icon.name
    
    def get_icon_path(self, icon_name: str, theme_name: str = None) -> str:
        """获取图标文件的完整路径"""
        theme_name = theme_name or self.active_theme
        theme = self.icon_themes.get(theme_name)
        if not theme:
            theme = self.icon_themes.get("default")
        
        # 查找图标映射
        icon_mapping = None
        for mapping in self.icon_mappings:
            if mapping.name == icon_name:
                icon_mapping = mapping
                break
        
        if not icon_mapping and icon_name == self.default_icon.name:
            icon_mapping = self.default_icon
        
        if not icon_mapping:
            return ""
        
        icon_path = Path(theme.base_path) / icon_mapping.icon_file
        
        # 如果图标文件不存在，尝试使用回退主题
        if not icon_path.exists() and theme.fallback_theme:
            return self.get_icon_path(icon_name, theme.fallback_theme)
        
        return str(icon_path)
    
    def get_char_fallback(self, icon_name: str) -> str:
        """获取字符回退图标"""
        for mapping in self.icon_mappings:
            if mapping.name == icon_name:
                return mapping.char_fallback
        
        if icon_name == self.default_icon.name:
            return self.default_icon.char_fallback
        
        return self.default_icon.char_fallback
    
    def get_char_icon(self, icon_name: str) -> str:
        """获取字符图标（别名方法）"""
        return self.get_char_fallback(icon_name)
    
    def set_active_theme(self, theme_name: str):
        """设置当前活动主题"""
        if theme_name in self.icon_themes and theme_name != self.active_theme:
            self.active_theme = theme_name
            self.config["active_theme"] = theme_name
            self._save_config()
            self.theme_changed.emit(theme_name)
    
    def get_available_themes(self) -> List[IconTheme]:
        """获取所有可用的主题"""
        return list(self.icon_themes.values())
    
    def add_icon_mapping(self, mapping: IconMapping):
        """添加新的图标映射"""
        self.icon_mappings.append(mapping)
        self._rebuild_lookup_tables()
        self._save_config()
    
    def remove_icon_mapping(self, icon_name: str) -> bool:
        """删除图标映射"""
        for i, mapping in enumerate(self.icon_mappings):
            if mapping.name == icon_name:
                del self.icon_mappings[i]
                self._rebuild_lookup_tables()
                self._save_config()
                return True
        return False
    
    # def _rebuild_lookup_tables(self):
    #     """重建快速查找表"""
    #     self.ext_to_icon.clear()
    #     self.filename_to_icon.clear()
    #     self.property_to_icon.clear()
    #     self._build_lookup_tables()
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            # 将数据类转换为字典
            config = {
                "icon_themes": {
                    name: {
                        "name": theme.name,
                        "display_name": theme.display_name,
                        "base_path": theme.base_path,
                        "fallback_theme": theme.fallback_theme
                    } for name, theme in self.icon_themes.items()
                },
                "active_theme": self.active_theme,
                "icon_mappings": [
                    {
                        "name": mapping.name,
                        "display_name": mapping.display_name,
                        "icon_file": mapping.icon_file,
                        "char_fallback": mapping.char_fallback,
                        "match_rules": [
                            {
                                "type": rule.type,
                                "patterns": rule.patterns,
                                "priority": rule.priority,
                                "property": rule.property,
                                "value": rule.value,
                                "case_sensitive": rule.case_sensitive
                            } for rule in mapping.match_rules
                        ]
                    } for mapping in self.icon_mappings
                ],
                "default_icon": {
                    "name": self.default_icon.name,
                    "display_name": self.default_icon.display_name,
                    "icon_file": self.default_icon.icon_file,
                    "char_fallback": self.default_icon.char_fallback
                }
            }
            
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")