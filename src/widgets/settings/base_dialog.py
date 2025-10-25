from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTabWidget, QMessageBox, QLabel, QFileDialog)
from PySide6.QtCore import Signal, Qt
import os

class BaseSettingsDialog(QDialog):
    """设置对话框基类"""
    
    # 设置已更改信号
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None, config_manager=None, language_manager=None):
        super().__init__(parent)
        self.parent_window = parent
        self.config_manager = config_manager
        self.language_manager = language_manager
        self.widgets = {}  # 存储所有控件的字典
        self.translation = self.language_manager.get_component_translation("settings") if self.language_manager else {}
        self.setWindowTitle(self.translation.get("dialog_title", "设置"))
        self.resize(600, 500)
        self._setup_ui()
        self._add_tabs()
        self._connect_signals()
        self._load_settings()
        
    def _setup_ui(self):
        """设置UI"""
        # 创建标签页容器
        self.tab_widget = QTabWidget()
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        self.btn_apply = QPushButton(self.translation.get("btn_apply", "应用"))
        self.btn_ok = QPushButton(self.translation.get("btn_ok", "确定"))
        self.btn_cancel = QPushButton(self.translation.get("btn_cancel", "取消"))
        
        button_layout.addStretch()
        button_layout.addWidget(self.btn_apply)
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)
        main_layout.addLayout(button_layout)
        
        # 连接按钮信号
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_apply.clicked.connect(self.apply_settings)
        
    def _add_tabs(self):
        """添加标签页 - 由子类实现"""
        pass
        
    def _create_modified_indicator(self, name):
        """创建修改状态指示器（星号标签）"""
        label = QLabel("*")
        label.setStyleSheet("color: red; font-weight: bold;")
        label.setVisible(False)  # 默认隐藏
        label.setFixedWidth(20)  # 设置固定宽度避免界面错乱
        # 将修改状态指示器存储到widgets字典中
        self.widgets[f'{name}_modified'] = label
        return label
        
    def _connect_signals(self):
        """连接信号 - 由子类实现"""
        pass
        
    def _connect_modified_signal(self, widget, config_key, default_value=None):
        """连接控件的修改信号到统一的处理函数"""
        if hasattr(widget, 'textChanged'):
            widget.textChanged.connect(lambda text, key=config_key, default=default_value: self._on_setting_changed(key, text, default))
        elif hasattr(widget, 'stateChanged'):
            widget.stateChanged.connect(lambda state, key=config_key, default=default_value: self._on_setting_changed(key, bool(state), default))
        elif hasattr(widget, 'valueChanged'):
            widget.valueChanged.connect(lambda value, key=config_key, default=default_value: self._on_setting_changed(key, value, default))
        elif hasattr(widget, 'currentIndexChanged'):
            widget.currentIndexChanged.connect(lambda index, key=config_key, default=default_value, widget=widget: self._on_setting_changed(key, widget.currentData() if widget.currentData() is not None else widget.currentText(), default))
            
    def _on_setting_changed(self, config_key, current_value, default_value=None):
        """统一处理设置项变化的函数"""
        # 获取对应的修改状态指示器
        modified_indicator_key = f"{config_key}_modified"
        if modified_indicator_key in self.widgets:
            # 检查配置键是否存在
            if self.config_manager and config_key in self.config_manager.config:
                config_value = self.config_manager.get(config_key)
            else:
                # 如果配置键不存在，则不显示修改指示器
                self.widgets[modified_indicator_key].setVisible(False)
                return
                
            # 检查当前值是否与配置文件中的值不同
            # 如果配置值为空且当前值也为空，则不显示修改标记
            if (current_value == "" or current_value is None) and (config_value == "" or config_value is None):
                is_modified = False
            # 对于布尔值，需要特殊处理确保正确比较
            elif isinstance(current_value, bool):
                is_modified = current_value != config_value
            # 对于日志级别，需要特殊处理大小写问题
            elif config_key == "log_level":
                # 将配置值和当前值都转换为大写进行比较
                is_modified = str(current_value).upper() != str(config_value).upper()
            else:
                is_modified = current_value != config_value
            self.widgets[modified_indicator_key].setVisible(is_modified)
                
    def _load_settings(self):
        """加载设置 - 由子类实现"""
        pass
        
    def _save_settings(self):
        """保存设置 - 由子类实现"""
        pass
        
    def _browse_folder(self, current_path="", title="选择文件夹"):
        """浏览文件夹"""
        if not current_path:
            current_path = os.getcwd()
        folder = QFileDialog.getExistingDirectory(self, title, current_path)
        return folder if folder else None
    
    def _browse_file(self, current_path="", title="选择文件", file_filter="所有文件 (*.*)"):
        """浏览文件"""
        if not current_path:
            current_path = os.getcwd()
        file_path, _ = QFileDialog.getOpenFileName(self, title, current_path, file_filter)
        return file_path if file_path else None
        

        
    def apply_settings(self):
        """应用设置"""
        try:
            # 保存设置
            self._save_settings()
            
            # 发出设置已更改信号
            if self.config_manager:
                self.settings_changed.emit(self.config_manager.config)
                
            # 隐藏所有修改指示器
            for key in self.widgets.keys():
                modified_indicator_key = f"{key}_modified"
                if modified_indicator_key in self.widgets:
                    self.widgets[modified_indicator_key].hide()
                    
            QMessageBox.information(self, self.translation.get("dlg_info", "信息"), 
                                  self.translation.get("dlg_settings_applied", "设置已应用"))
            return True
        except Exception as e:
            QMessageBox.critical(self, self.translation.get("error", "错误"), 
                               self.translation.get("apply_settings_failed", "应用设置失败") + f": {str(e)}")
            return False
            
    def accept(self):
        """确认对话框"""
        if self.apply_settings():
            super().accept()
    
    def reject(self):
        """取消对话框 - 清理资源"""
        # 清理修改指示器
        for key in list(self.widgets.keys()):
            if key.endswith('_modified'):
                try:
                    self.widgets[key].deleteLater()
                    del self.widgets[key]
                except:
                    pass
        
        # 立即清理引用，避免内存波动
        self._immediate_cleanup()
        
        super().reject()
    
    def _immediate_cleanup(self):
        """立即清理可以释放的资源"""
        # 清理标签页引用
        if hasattr(self, 'tab_widget'):
            # 清理所有标签页
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if widget:
                    # 清理标签页内的控件引用
                    if hasattr(widget, 'widgets'):
                        widget.widgets.clear()
            self.tab_widget.clear()
        
        # 清理主要的控件引用
        if hasattr(self, 'widgets'):
            # 只清理修改指示器，保留主要控件让PySide6自己管理
            for key in list(self.widgets.keys()):
                if key.endswith('_modified'):
                    try:
                        self.widgets[key].deleteLater()
                    except:
                        pass
    
    def __del__(self):
        """析构函数 - 确保资源被正确清理"""
        try:
            # 清理控件引用
            if hasattr(self, 'widgets'):
                for widget in self.widgets.values():
                    try:
                        widget.deleteLater()
                    except:
                        pass
                self.widgets.clear()
                del self.widgets
            # 清理父窗口引用
            if hasattr(self, 'parent_window'):
                del self.parent_window
            # 清理配置管理器引用
            if hasattr(self, 'config_manager'):
                del self.config_manager
            # 清理语言管理器引用
            if hasattr(self, 'language_manager'):
                del self.language_manager
        except:
            pass  # 忽略清理过程中的错误