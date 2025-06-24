import os
from PySide6.QtWidgets import QMessageBox

class HomeHandler:
    def __init__(self, main_window):
        self.main_window = main_window
        # 定义 home_path（项目目录下的 "home" 文件夹）
        self.home_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "home")
        # 确保 home 文件夹存在（若不存在则创建）
        os.makedirs(self.home_path, exist_ok=True)

    def navigate_home(self):
        """导航到 home 文件夹并刷新文件列表"""
        if not os.path.exists(self.home_path):
            os.makedirs(self.home_path, exist_ok=True)
            
        self.main_window.current_path = self.home_path
        self.main_window.address_bar.setText("home 目录")
        self.main_window.update_filelist()
