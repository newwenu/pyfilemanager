import os

# 导入事件总线
from core import event_bus


class HomeHandler:
    """主页处理器 - 使用事件总线解耦"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        # 定义 home_path（项目目录下的 "home" 文件夹）
        home_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "..", "..", "home"
        )
        self.home_path = os.path.normpath(home_path)
        # 确保 home 文件夹存在（若不存在则创建）
        os.makedirs(self.home_path, exist_ok=True)

    def navigate_home(self):
        """导航到 home 文件夹（使用事件总线）"""
        if not os.path.exists(self.home_path):
            os.makedirs(self.home_path, exist_ok=True)
        
        # 使用事件总线导航到 home 目录
        event_bus.navigate_to.emit(self.home_path)
        # 设置地址栏显示文本
        self.main_window.address_bar.setText("home 目录")
