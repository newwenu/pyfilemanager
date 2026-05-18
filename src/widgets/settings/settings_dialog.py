from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QCheckBox, QLineEdit, QSpinBox, QComboBox, QGroupBox
from PySide6.QtCore import Qt
from .base_dialog import BaseSettingsDialog
from .tabs.general_tab import GeneralTab
from .tabs.appearance_tab import AppearanceTab
from .tabs.advanced_tab import AdvancedTab
from .tabs.context_menu_tab import ContextMenuTab
from .tabs.icon_manager_tab import IconManagerTab
from .tabs.scan_exclude_tab import ScanExcludeTab

class SettingsDialog(BaseSettingsDialog):
    """设置对话框主类"""
    
    def __init__(self, parent=None, config_manager=None, language_manager=None):
        super().__init__(parent, config_manager, language_manager)
        # 保存原始配置值用于修改判断
        self._original_config = {}
        if self.config_manager:
            self._original_config = self.config_manager.config.copy()
    
    def __del__(self):
        """析构函数 - 确保资源被正确清理"""
        try:
            # 清理子标签页引用
            if hasattr(self, 'general_tab'):
                del self.general_tab
            if hasattr(self, 'appearance_tab'):
                del self.appearance_tab
            if hasattr(self, 'context_menu_tab'):
                del self.context_menu_tab
            if hasattr(self, 'advanced_tab'):
                del self.advanced_tab
            # 清理控件字典
            if hasattr(self, 'widgets'):
                self.widgets.clear()
                del self.widgets
            # 清理原始配置引用
            if hasattr(self, '_original_config'):
                self._original_config.clear()
                del self._original_config
        except:
            pass  # 忽略清理过程中的错误
        
    def _add_tabs(self):
        """添加标签页"""
        # 常规设置标签页
        self.general_tab = GeneralTab(
            parent=self,
            config=self.config_manager.config if self.config_manager else {},
            widgets=self.widgets,
            translation=self.translation
        )
        self.tab_widget.addTab(self.general_tab, self.translation.get("tab_general", "常规"))
        
        # 外观设置标签页
        self.appearance_tab = AppearanceTab(
            parent=self,
            config=self.config_manager.config if self.config_manager else {},
            widgets=self.widgets,
            translation=self.translation
        )
        self.tab_widget.addTab(self.appearance_tab, self.translation.get("tab_appearance", "外观"))
        
        # 右键菜单设置标签页
        self.context_menu_tab = ContextMenuTab(
            parent=self,
            config=self.config_manager.config if self.config_manager else {},
            widgets=self.widgets,
            translation=self.translation
        )
        self.tab_widget.addTab(self.context_menu_tab, self.translation.get("tab_context_menu", "右键菜单"))
        
        # 高级设置标签页
        self.advanced_tab = AdvancedTab(
            parent=self,
            config=self.config_manager.config if self.config_manager else {},
            widgets=self.widgets,
            translation=self.translation
        )
        self.tab_widget.addTab(self.advanced_tab, self.translation.get("tab_advanced", "高级"))

        # 图标管理标签页
        self.icon_manager_tab = IconManagerTab(
            parent=self,
            config=self.config_manager.config if self.config_manager else {},
            widgets=self.widgets,
            translation=self.translation
        )
        self.tab_widget.addTab(self.icon_manager_tab, self.translation.get("tab_icon_manager", "图标管理"))

        # 扫描排除标签页
        self.scan_exclude_tab = ScanExcludeTab(
            parent=self,
            config=self.config_manager.config if self.config_manager else {},
            widgets=self.widgets,
            translation=self.translation
        )
        self.tab_widget.addTab(self.scan_exclude_tab, self.translation.get("tab_scan_exclude", "扫描排除"))
    
    def _connect_signals(self):
        """连接信号 - 标签页内部已处理"""
        pass
        
    def _on_setting_changed(self, config_key, current_value, default_value=None):
        """统一处理设置项变化的函数"""
        # 获取对应的修改状态指示器
        modified_indicator_key = f"{config_key}_modified"
        if modified_indicator_key in self.widgets:
            # 获取原始配置值（而不是实时更新的配置值）
            config_value = self._original_config.get(config_key, default_value)
            
            # 检查当前值是否与原始配置值不同
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
        
        # 如果配置管理器可用，更新配置
        if self.config_manager:
            if current_value is not None:
                self.config_manager.set_setting(config_key, current_value)
            else:
                # 从控件获取当前值
                widget = self.widgets.get(config_key)
                if widget:
                    if isinstance(widget, QCheckBox):
                        value = widget.isChecked()
                    elif isinstance(widget, QLineEdit):
                        value = widget.text()
                    elif isinstance(widget, QSpinBox):
                        value = widget.value()
                    elif isinstance(widget, QComboBox):
                        value = widget.itemData(widget.currentIndex())
                    
                    if value is not None:
                        self.config_manager.set_setting(config_key, value)
    

    
    def _load_settings(self):
        """加载设置 - 标签页构造函数中已处理"""
        # 初始化修改指示器字典
        self.modified_indicators = {}
        pass
    
    def _save_settings(self):
        """保存设置 - 只保存原始配置中存在的设置项"""
        if not self.config_manager:
            return
            
        # 获取原始配置中的所有键
        original_keys = set(self._original_config.keys())
        
        # 收集所有设置，但只保留原始配置中存在的键
        settings_to_save = {}
        
        # 常规设置
        if hasattr(self.general_tab, 'widgets'):
            for key, widget in self.general_tab.widgets.items():
                if key in original_keys:  # 只保存原始配置中存在的设置
                    if isinstance(widget, QCheckBox):
                        settings_to_save[key] = widget.isChecked()
                    elif isinstance(widget, QLineEdit):
                        settings_to_save[key] = widget.text()
                    elif isinstance(widget, QSpinBox):
                        settings_to_save[key] = widget.value()
        
        # 外观设置
        if hasattr(self.appearance_tab, 'widgets'):
            for key, widget in self.appearance_tab.widgets.items():
                if key in original_keys:  # 只保存原始配置中存在的设置
                    if isinstance(widget, QCheckBox):
                        settings_to_save[key] = widget.isChecked()
                    elif isinstance(widget, QLineEdit):
                        settings_to_save[key] = widget.text()
                    elif isinstance(widget, QSpinBox):
                        settings_to_save[key] = widget.value()
                    elif isinstance(widget, QComboBox):
                        settings_to_save[key] = widget.itemData(widget.currentIndex())
        
        # 右键菜单设置
        if hasattr(self.context_menu_tab, 'widgets'):
            for key, widget in self.context_menu_tab.widgets.items():
                if key in original_keys:  # 只保存原始配置中存在的设置
                    if isinstance(widget, QCheckBox):
                        settings_to_save[key] = widget.isChecked()
                    elif isinstance(widget, QLineEdit):
                        settings_to_save[key] = widget.text()
                    elif isinstance(widget, QSpinBox):
                        settings_to_save[key] = widget.value()
                    elif isinstance(widget, QComboBox):
                        settings_to_save[key] = widget.itemData(widget.currentIndex())
        
        # 高级设置
        if hasattr(self.advanced_tab, 'widgets'):
            for key, widget in self.advanced_tab.widgets.items():
                if key in original_keys:  # 只保存原始配置中存在的设置
                    if isinstance(widget, QCheckBox):
                        settings_to_save[key] = widget.isChecked()
                    elif isinstance(widget, QLineEdit):
                        settings_to_save[key] = widget.text()
                    elif isinstance(widget, QSpinBox):
                        settings_to_save[key] = widget.value()
                    elif isinstance(widget, QComboBox):
                        settings_to_save[key] = widget.itemData(widget.currentIndex())

        # 图标管理设置
        if hasattr(self, 'icon_manager_tab'):
            self.icon_manager_tab.save_settings()

        # 扫描排除设置
        if hasattr(self, 'scan_exclude_tab'):
            exclude_settings = self.scan_exclude_tab.get_exclude_settings()
            for key, value in exclude_settings.items():
                self.config_manager.set_setting(key, value)

        # 保存到配置管理器
        for key, value in settings_to_save.items():
            self.config_manager.set_setting(key, value)
        
        # 保存配置文件
        self.config_manager.save_config()
        
        # 应用日志级别变更（实时生效）
        if 'log_level' in settings_to_save:
            from utils.logging_config import update_log_level
            update_log_level(settings_to_save['log_level'])