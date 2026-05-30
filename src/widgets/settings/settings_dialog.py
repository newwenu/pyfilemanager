from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTabWidget, QLabel, QFileDialog, QCheckBox, QLineEdit,
                               QSpinBox, QComboBox, QGroupBox)
from PySide6.QtCore import Signal, Qt
from core.config_provider import config_provider
from .tabs.general_tab import GeneralTab
from .tabs.appearance_tab import AppearanceTab
from .tabs.advanced_tab import AdvancedTab
from .tabs.context_menu_tab import ContextMenuTab
from .tabs.icon_manager_tab import IconManagerTab
from .tabs.scan_exclude_tab import ScanExcludeTab
import os


class SettingsDialog(QDialog):
    """设置对话框主类

    使用 ConfigProvider 的临时编辑会话机制：
    - 打开对话框时 begin_session()，所有修改只保存在内存
    - 点击"确定"/"应用"时 commit_session() 提交到磁盘
    - 点击"取消"时 rollback_session() 撤销所有修改
    """

    settings_changed = Signal(dict)

    def __init__(self, parent=None, config_manager=None, language_manager=None):
        super().__init__(parent)
        self.parent_window = parent
        self.config_manager = config_manager
        self.language_manager = language_manager
        self.widgets = {}
        self.translation = self.language_manager.get_component_translation("settings") if self.language_manager else {}

        # 开始临时编辑会话，获取原始配置快照
        self._original_config = config_provider.begin_session()

        self.setWindowTitle(self.translation.get("dialog_title", "设置"))
        self.resize(600, 500)
        self._setup_ui()
        self._add_tabs()

    def _setup_ui(self):
        """设置UI"""
        self.tab_widget = QTabWidget()

        button_layout = QHBoxLayout()
        self.btn_apply = QPushButton(self.translation.get("btn_apply", "应用"))
        self.btn_ok = QPushButton(self.translation.get("btn_ok", "确定"))
        self.btn_cancel = QPushButton(self.translation.get("btn_cancel", "取消"))

        button_layout.addStretch()
        button_layout.addWidget(self.btn_apply)
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)
        main_layout.addLayout(button_layout)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_apply.clicked.connect(self.apply_settings)

    def _add_tabs(self):
        """添加标签页"""
        cfg = config_provider.get_config()

        # 常规设置标签页
        self.general_tab = GeneralTab(
            parent=self,
            config=cfg,
            widgets=self.widgets,
            translation=self.translation
        )
        self.tab_widget.addTab(self.general_tab, self.translation.get("tab_general", "常规"))

        # 外观设置标签页
        self.appearance_tab = AppearanceTab(
            parent=self,
            config=cfg,
            widgets=self.widgets,
            translation=self.translation
        )
        self.tab_widget.addTab(self.appearance_tab, self.translation.get("tab_appearance", "外观"))

        # 右键菜单设置标签页
        self.context_menu_tab = ContextMenuTab(
            parent=self,
            config=cfg,
            widgets=self.widgets,
            translation=self.translation
        )
        self.tab_widget.addTab(self.context_menu_tab, self.translation.get("tab_context_menu", "右键菜单"))

        # 高级设置标签页
        self.advanced_tab = AdvancedTab(
            parent=self,
            config=cfg,
            widgets=self.widgets,
            translation=self.translation
        )
        self.tab_widget.addTab(self.advanced_tab, self.translation.get("tab_advanced", "高级"))

        # 图标管理标签页
        self.icon_manager_tab = IconManagerTab(
            parent=self,
            config=cfg,
            widgets=self.widgets,
            translation=self.translation
        )
        self.tab_widget.addTab(self.icon_manager_tab, self.translation.get("tab_icon_manager", "图标管理"))

        # 扫描排除标签页
        self.scan_exclude_tab = ScanExcludeTab(
            parent=self,
            config=cfg,
            widgets=self.widgets,
            translation=self.translation
        )
        self.tab_widget.addTab(self.scan_exclude_tab, self.translation.get("tab_scan_exclude", "扫描排除"))

    def _create_modified_indicator(self, name):
        """创建修改状态指示器（星号标签）"""
        label = QLabel("*")
        label.setStyleSheet("color: red; font-weight: bold;")
        label.setVisible(False)
        label.setFixedWidth(20)
        self.widgets[f'{name}_modified'] = label
        return label

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
            self._save_settings()
            config_provider.commit_session(emit_event=True)

            from image_manager.icon_settings_manager import get_icon_settings_manager
            icon_settings_manager = get_icon_settings_manager()
            icon_settings_manager.reload_settings()

            self.settings_changed.emit(config_provider.get_all())

            # 更新会话快照，将当前配置作为新的对比基准
            config_provider.update_session_snapshot()

            # 隐藏所有修改指示器
            for key in list(self.widgets.keys()):
                if key.endswith('_modified'):
                    self.widgets[key].hide()

            return True
        except Exception as e:
            if hasattr(self.parent_window, 'show_settings_tip'):
                self.parent_window.show_settings_tip(
                    self.translation.get("apply_settings_failed", "应用设置失败") + f": {str(e)}", 3000, "error"
                )
            return False

    def _on_setting_changed(self, config_key, current_value, default_value=None):
        """处理设置项变化，更新星形指示器（兼容旧 Tab）"""
        from core.config_provider import config_provider
        modified_indicator_key = f"{config_key}_modified"
        if modified_indicator_key in self.widgets:
            # 更新 config_provider
            config_provider.set(config_key, current_value, emit_event=False)
            # 获取会话快照中的值
            snapshot_value = config_provider.get_session_snapshot(config_key, default_value)
            # 对比当前值与会话快照值
            if isinstance(current_value, bool):
                is_modified = current_value != snapshot_value
            else:
                is_modified = current_value != snapshot_value
            self.widgets[modified_indicator_key].setVisible(is_modified)

    def accept(self):
        """确认对话框"""
        if self.apply_settings():
            super().accept()

    def reject(self):
        """取消对话框 - 撤销所有修改并清理资源"""
        # 回滚临时编辑会话，恢复原始配置
        config_provider.rollback_session()
        super().reject()

    def __del__(self):
        """析构函数 - 确保资源被正确清理"""
        try:
            # 如果会话仍处于活跃状态（异常关闭等情况），自动回滚
            if config_provider.is_session_active():
                config_provider.rollback_session()

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

    def _save_settings(self):
        """保存设置 - 收集各 Tab 的值并同步到 ConfigProvider

        由于使用了临时编辑会话，这里只需把各 Tab 控件的最新值同步到
        ConfigProvider，最后统一 commit_session() 即可。
        """
        # 获取原始配置中的所有键（用于过滤）
        original_keys = set(self._original_config.keys())

        # 收集所有设置，但只保留原始配置中存在的键
        settings_to_save = {}

        # 常规设置
        if hasattr(self.general_tab, 'widgets'):
            for key, widget in self.general_tab.widgets.items():
                if key in original_keys:
                    if isinstance(widget, QCheckBox):
                        settings_to_save[key] = widget.isChecked()
                    elif isinstance(widget, QLineEdit):
                        settings_to_save[key] = widget.text()
                    elif isinstance(widget, QSpinBox):
                        settings_to_save[key] = widget.value()

        # 外观设置
        if hasattr(self.appearance_tab, 'widgets'):
            for key, widget in self.appearance_tab.widgets.items():
                if key in original_keys:
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
                if key in original_keys:
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
                if key in original_keys:
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
                config_provider.set(key, value, emit_event=False)

        # 同步所有收集到的设置到 ConfigProvider（会话期间不落盘）
        for key, value in settings_to_save.items():
            config_provider.set(key, value, emit_event=False)

        # 应用日志级别变更（实时生效）
        if 'log_level' in settings_to_save:
            from utils.logging_config import update_log_level
            update_log_level(settings_to_save['log_level'])
