# 新增：独立配置管理模块
import json
import os

class ConfigManager:
    def __init__(self, config_path="config/setting1.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """私有方法：实际加载配置（隐藏实现细节）"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("警告：未找到config.json，将使用默认配置")
            return {}
        except json.JSONDecodeError:
            print("警告：config.json格式错误，将使用默认配置")
            return {}

    def get(self, key, default=None):
        """公共接口：获取配置值（暴露简单接口）"""
        return self.config.get(key, default)
