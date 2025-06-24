import sys
from PySide6.QtWidgets import QApplication
from main_window2 import FileManager
from utils.config_manager import ConfigManager  # 新增导入

if __name__ == "__main__":
    # 初始化配置管理器（自动加载配置）
    config_manager = ConfigManager()  # 正确创建 ConfigManager 实例
    app = QApplication(sys.argv)
    # 传递 ConfigManager 实例给 FileManager
    window = FileManager("media/background.png", config_manager)  # 修正此处
    window.show()
    sys.exit(app.exec())