import sys
sys.path.append("src")
from PySide6.QtWidgets import QApplication
from src.main_window2 import FileManager
from src.utils.config_manager import ConfigManager  # 导入


if __name__ == "__main__":
    # 初始化配置管理器（自动加载配置）
    config_manager = ConfigManager("userdata/config/setting1.json")  # 创建 ConfigManager 实例
    app = QApplication(sys.argv)
    # 传递 ConfigManager 实例给 FileManager
    background_image = config_manager.config["background_image"]
    window = FileManager(background_image, config_manager)
    window.show()
    sys.exit(app.exec())