"""
设置对话框管理器 - 单例模式管理设置对话框生命周期
负责管理设置对话框的创建、显示和清理，避免内存泄漏
"""

import weakref
import gc
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog
from tip_manager.tip_manager_proxy import TipManager


class SettingsDialogManager(QObject):
    """设置对话框管理器 - 单例模式"""
    
    # 设置改变信号 - 转发自对话框
    settings_changed = Signal(dict)
    
    _instance = None
    
    def __new__(cls, parent=None, config_manager=None, language_manager=None):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, parent=None, config_manager=None, language_manager=None):
        """初始化设置对话框管理器"""
        if self._initialized:
            return
            
        super().__init__(parent)
        self._parent = parent
        self._config_manager = config_manager
        self._language_manager = language_manager
        self._dialog_ref = None  # 弱引用到当前对话框
        self._initialized = True
        self._enable_memory_tracking = False  # 内存跟踪开关
    
    @classmethod
    def get_instance(cls, parent=None, config_manager=None, language_manager=None):
        """获取管理器实例"""
        if cls._instance is None:
            cls._instance = cls(parent, config_manager, language_manager)
        return cls._instance
    
    def show_settings_dialog(self):
        """显示设置对话框 - 使用单例模式避免重复创建"""
        # 可选：记录当前内存使用
        if self._enable_memory_tracking:
            try:
                import psutil
                process = psutil.Process()
                self._mem_before = process.memory_info().rss / 1024 / 1024
                print(f"打开对话框前内存: {self._mem_before:.2f} MB")
            except:
                self._mem_before = 0
        
        # 清理已存在的对话框
        self._cleanup_existing_dialog()
        
        # 延迟导入避免循环依赖
        from widgets.settings_dialog_model import SettingsDialog
        
        # 创建新的对话框实例
        dialog = SettingsDialog(self._parent, self._config_manager, self._language_manager)
        
        # 连接信号 - 转发设置改变信号
        dialog.settings_changed.connect(self._on_settings_changed)
        
        # 连接finished信号进行自动清理
        dialog.finished.connect(self._on_dialog_finished)
        
        # 使用弱引用存储对话框引用
        self._dialog_ref = weakref.ref(dialog)
        
        # 显示对话框 - 使用exec()创建模态对话框，避免显示在任务栏
        dialog.exec()
    
    def _cleanup_existing_dialog(self):
        """清理已存在的对话框"""
        if self._dialog_ref is not None:
            dialog = self._dialog_ref()
            if dialog is not None:
                try:
                    # 断开信号
                    dialog.settings_changed.disconnect(self._on_settings_changed)
                    # 断开finished信号
                    try:
                        dialog.finished.disconnect(self._on_dialog_finished)
                    except:
                        pass
                    # 清理对话框的子对象
                    if hasattr(dialog, 'tab_widget'):
                        # 清理标签页
                        for i in range(dialog.tab_widget.count()):
                            widget = dialog.tab_widget.widget(i)
                            if widget:
                                # 清理标签页内的控件
                                if hasattr(widget, 'widgets'):
                                    for w in widget.widgets.values():
                                        try:
                                            w.deleteLater()
                                        except:
                                            pass
                                    widget.widgets.clear()
                                widget.deleteLater()
                        dialog.tab_widget.clear()
                    # 延迟删除对话框
                    dialog.deleteLater()
                except:
                    pass  # 忽略清理过程中的错误
            self._dialog_ref = None
    
    def _on_settings_changed(self, new_config):
        """转发设置改变信号"""
        self.settings_changed.emit(new_config)
        
        # 使用全局TipManager显示设置保存成功的提示
        if self._parent:
            # 获取翻译文本
            if self._language_manager:
                translation = self._language_manager.get_translation()
                # 获取设置部分的翻译
                settings_translation = translation.get("settings", {})
                message = settings_translation.get("dlg_settings_applied", "设置已应用")
            else:
                message = "设置已应用"
            
            TipManager.show_success(
                self._parent,
                message,
                duration=2000
            )
    
    def _on_dialog_finished(self):
        """对话框关闭时的清理"""
        # 延迟清理确保对话框完全关闭
        from PySide6.QtCore import QTimer
        # 使用更长的延迟确保对话框完全销毁
        QTimer.singleShot(100, self._delayed_cleanup)
    
    def _delayed_cleanup(self):
        """延迟清理"""
        self._cleanup_existing_dialog()
        
        # 注意：不要清理父窗口引用，否则后续对话框会失去父窗口
        # 父窗口引用需要在管理器生命周期内保持有效
        
        # 强制垃圾回收两次以确保完全清理
        gc.collect()
        gc.collect()  # 第二次收集处理循环引用
        
        # 可选：打印内存使用信息（调试用）
        if self._enable_memory_tracking:
            try:
                import psutil
                process = psutil.Process()
                mem_after = process.memory_info().rss / 1024 / 1024
                print(f"清理后内存使用: {mem_after:.2f} MB")
                print(f"内存变化: {mem_after - getattr(self, '_mem_before', 0):.2f} MB")
            except:
                pass
    
    def set_memory_tracking(self, enabled):
        """设置内存跟踪开关"""
        self._enable_memory_tracking = enabled
        
    def cleanup(self):
        """清理管理器资源"""
        self._cleanup_existing_dialog()
        
        # 强制垃圾回收
        gc.collect()
    
    def __del__(self):
        """析构函数 - 确保资源被清理"""
        try:
            self.cleanup()
        except:
            pass  # 忽略清理过程中的错误