"""
图标设置管理器
管理图标相关的设置，包括是否使用系统图标等
"""
import os
import json
from typing import List, Set, Optional


class IconSettingsManager:
    """图标设置管理器 - 单例模式"""

    _instance = None
    _config_manager = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._settings = {}
        self._load_settings()
        self._initialized = True

    def set_config_manager(self, config_manager):
        """设置配置管理器"""
        IconSettingsManager._config_manager = config_manager
        self._load_settings()

    def _load_settings(self):
        """加载设置 - 优先从主配置读取"""
        default_settings = {
            "use_system_icons_for_extensions": [".exe", ".bat", ".cmd", ".msi", ".com", ".dll"],
            "use_system_icons_for_default": True
        }

        # 优先从主配置读取
        if self._config_manager and hasattr(self._config_manager, 'config'):
            config = self._config_manager.config
            has_settings = False
            self._settings = {}
            
            if 'use_system_icons_for_extensions' in config:
                self._settings["use_system_icons_for_extensions"] = config['use_system_icons_for_extensions']
                has_settings = True
            else:
                self._settings["use_system_icons_for_extensions"] = default_settings["use_system_icons_for_extensions"]
            
            if 'use_system_icons_for_default' in config:
                self._settings["use_system_icons_for_default"] = config['use_system_icons_for_default']
                has_settings = True
            else:
                self._settings["use_system_icons_for_default"] = default_settings["use_system_icons_for_default"]
            
            if not has_settings:
                # 保存到主配置
                self._save_to_config(default_settings)
        else:
            # 回退到独立配置文件
            config_path = os.path.join("userdata", "file-icon_type", "icon_settings.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self._settings = json.load(f)
                        # 合并默认设置
                        for key, value in default_settings.items():
                            if key not in self._settings:
                                self._settings[key] = value
                except Exception as e:
                    print(f"加载图标设置失败: {e}")
                    self._settings = default_settings
            else:
                self._settings = default_settings

    def _save_to_config(self, settings):
        """保存到主配置"""
        if self._config_manager and hasattr(self._config_manager, 'config'):
            self._config_manager.config.update(settings)
            if hasattr(self._config_manager, 'save_config'):
                self._config_manager.save_config()
            # 重新加载设置以确保立即生效
            self._load_settings()

    def _save_settings(self):
        """保存设置 - 保存到主配置"""
        # 保存到主配置
        self._save_to_config(self._settings)

        # 同时保存到独立文件作为备份
        try:
            config_path = os.path.join("userdata", "file-icon_type", "icon_settings.json")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存图标设置到文件失败: {e}")

    def get_use_system_icons_extensions(self) -> List[str]:
        """获取使用系统图标的扩展名列表"""
        return self._settings.get("use_system_icons_for_extensions", [".exe", ".bat", ".cmd", ".msi", ".com", ".dll"])

    def get_use_system_icons_set(self) -> Set[str]:
        """获取使用系统图标的扩展名集合（用于快速查找）"""
        return set(self.get_use_system_icons_extensions())

    def set_use_system_icons_extensions(self, extensions: List[str]):
        """设置使用系统图标的扩展名列表"""
        self._settings["use_system_icons_for_extensions"] = extensions
        self._save_settings()

    def is_use_system_icon(self, file_ext: str) -> bool:
        """检查指定扩展名是否使用系统图标"""
        # 确保扩展名以小写形式比较
        return file_ext.lower() in self.get_use_system_icons_set()

    def is_use_system_icon_for_default(self) -> bool:
        """检查default类型是否使用系统图标"""
        return self._settings.get("use_system_icons_for_default", True)

    def reload_settings(self):
        """重新加载设置（用于设置变更后）"""
        self._load_settings()


# 全局实例
_icon_settings_manager = None


def get_icon_settings_manager() -> IconSettingsManager:
    """获取图标设置管理器实例"""
    global _icon_settings_manager
    if _icon_settings_manager is None:
        _icon_settings_manager = IconSettingsManager()
    return _icon_settings_manager
