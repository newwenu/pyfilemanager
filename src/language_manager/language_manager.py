from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import sys
import os
import subprocess

class LanguageManager:
    def __init__(self, main_window, config_manager):
        self.main_window = main_window
        self.config_manager = config_manager
        self.lang = config_manager.config.get("language", "zh_CN")

    def set_language(self, lang: str):
        """修改语言配置并重启应用"""
        self.config_manager.config["language"] = lang
        self.config_manager.save_config()
        self._restart_app()

    # def _restart_app(self):
    #     """安全重启应用（确保定时器回调在事件循环中执行）"""
    #     # 延迟 500ms 启动新进程（事件循环保持运行）
    #     def start_new_process():
    #         print("启动新进程前")
    #         print("当前工作目录:", os.getcwd())
    #         print("当前脚本路径:", sys.argv[0])
    #         print("启动新进程")
    #         # 触发应用退出（在启动新进程后）
    #         QApplication.quit()
    #         # 启动独立新进程
    #         # cwd = os.getcwd()
    #         subprocess.Popen([sys.executable] + sys.argv, cwd=os.getcwd()).wait()
            
    #         # 原进程退出（确保不残留）
    #         sys.exit(0)
            
        
    #     # 设置定时器（事件循环保持运行直到回调执行）
    #     QTimer.singleShot(500, start_new_process)


    def _restart_app(self):
        """安全重启（延迟原进程退出，避免阻塞）"""
        def start_new_process():
            # print("启动新进程前")
            # print("当前工作目录:", os.getcwd())
            # print("当前脚本路径:", sys.argv[0])
            # print("启动新进程")
            
            # 启动新进程（不阻塞原进程）
            subprocess.Popen([sys.executable] + sys.argv, cwd=os.getcwd())
            
            # 延迟原进程退出（等待新进程初始化，如1秒）
            QTimer.singleShot(1000, lambda: (QApplication.quit(), sys.exit(0)))
        
        QTimer.singleShot(500, start_new_process)