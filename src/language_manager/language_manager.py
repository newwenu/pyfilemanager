from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from core.config_provider import config_provider
import sys
import os
import subprocess

class LanguageManager:
    def __init__(self, main_window, config_manager):
        self.main_window = main_window
        self.config_manager = config_manager
        self.lang = config_manager.config.get("language", "zh_CN")
        # 缓存已加载的翻译，避免重复加载
        self._translation_cache = None

    def set_language(self, lang: str):
        """修改语言配置并重启应用"""
        config_provider.set("language", lang)
        self._restart_app()

    def get_translation(self):
        """获取当前语言的翻译字典，提供统一简便的语言获取方法"""
        if self._translation_cache is None:
            self._translation_cache = self.config_manager.load_translation(self.lang)
        return self._translation_cache

    def get_component_translation(self, component_key):
        """获取指定组件的翻译字典"""
        translation = self.get_translation()
        return translation.get(component_key, {})

    def get_shortcut_translations(self):
        """获取当前语言的快捷键翻译字典"""
        translation = self.get_translation()
        return translation.get("shortcuts", {})

    def _restart_app(self):
        """安全重启（延迟原进程退出，避免阻塞）"""
        def start_new_process():
            
            # 启动新进程（不阻塞原进程）
            subprocess.Popen([sys.executable] + sys.argv, cwd=os.getcwd())
            
            # 延迟原进程退出（等待新进程初始化，如1秒）
            QTimer.singleShot(1000, lambda: (QApplication.quit(), sys.exit(0)))
        
        QTimer.singleShot(500, start_new_process)