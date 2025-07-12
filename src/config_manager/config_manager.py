# ：独立配置管理模块（已移动至config目录）
import json
import os
from pathlib import Path  # 新增：用于路径处理

class ConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self._load_config()  # 加载或创建配置文件

    def _load_config(self):
        """私有方法：加载配置（优化：文件不存在时自动创建默认配置）"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("警告：未找到配置文件，将创建默认配置...")
            # 自动创建默认配置文件
            default_config = {
                "window_title": "文件管理器",
                "initial_size": [900, 600],
                "file_list_bg_alpha": 100,
                "nav_tree_bg_alpha": 100,
                "background_image": "media/background.png",
                "background_alpha": 150,
                "font_size": 15,
                "font_family": "Microsoft YaHei",
                "nav_tree_icon_size": 60,
                "file_list_icon_size": 40,
                "drive_icon_size": 60,
                "file_list_font_size": 14,
                "nav_tree_font_size": 15,
                "Drive_font_size": 13,
                "show_hidden_files": False,
                "show_all_sizes": False,
                "statusbar_visible": True
            }
            # 创建配置文件目录（如果不存在）
            config_dir = os.path.dirname(self.config_path)
            Path(config_dir).mkdir(parents=True, exist_ok=True)
            # 写入默认配置
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print(f"成功创建默认配置文件：{self.config_path}")
            return default_config
        except json.JSONDecodeError:
            print("警告：配置文件格式错误，将使用空配置（请检查JSON语法）")
            return {}

    def get(self, key, default=None):
        """公共接口：获取配置值（暴露简单接口）"""
        return self.config.get(key, default)
