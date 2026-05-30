"""
设置项组辅助类 - 简化设置标签页的开发

提供统一的方式来创建带星形修改指示器的设置项，自动处理：
- 创建控件
- 创建星形指示器
- 注册到 widgets 字典
- 连接信号
"""
from typing import Optional, Any, Callable
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QCheckBox, QLineEdit, QSpinBox, QComboBox,
    QLabel, QLayout, QFormLayout
)
from PySide6.QtCore import Qt


class SettingItemGroup:
    """设置项组 - 管理一组设置项的创建和信号连接"""

    def __init__(self, tab_widget: QWidget):
        """
        初始化设置项组

        Args:
            tab_widget: 所属的标签页实例（如 GeneralTab、AppearanceTab 等）
        """
        self.tab = tab_widget
        self._settings_dialog = None

    def _get_settings_dialog(self):
        """获取设置对话框实例（带缓存）"""
        if self._settings_dialog is None:
            parent = self.tab.parent()
            while parent is not None:
                # 检查是否有创建指示器的方法（SettingsDialog 的特征）
                if hasattr(parent, '_create_modified_indicator'):
                    self._settings_dialog = parent
                    break
                parent = parent.parent()
        return self._settings_dialog

    def add_checkbox(
        self,
        parent_layout: QLayout,
        config_key: str,
        label: str,
        default_value: bool = False,
        tooltip: Optional[str] = None
    ) -> QCheckBox:
        """
        添加复选框设置项

        Args:
            parent_layout: 父布局
            config_key: 配置键名
            label: 显示文本
            default_value: 默认值
            tooltip: 提示文本

        Returns:
            创建的 QCheckBox 实例
        """
        checkbox = QCheckBox(label)
        checkbox.setChecked(self.tab.config.get(config_key, default_value))
        if tooltip:
            checkbox.setToolTip(tooltip)

        # 创建带星形指示器的行
        self._create_setting_row(parent_layout, config_key, checkbox)

        # 注册到 widgets
        self.tab.widgets[config_key] = checkbox

        # 连接信号
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            indicator_key = f"{config_key}_modified"
            def on_checkbox_changed(state, key=config_key, default=default_value, ind_key=indicator_key):
                # 注意：state 可能是整数或 Qt.CheckState 枚举值
                current_value = (state == Qt.CheckState.Checked) or (state == 2)
                # 更新 config_provider（会话期间不落盘）
                from core.config_provider import config_provider
                config_provider.set(key, current_value, emit_event=False)
                # 直接更新星形指示器（不依赖 settings_dialog）
                if ind_key in settings_dialog.widgets:
                    snapshot = config_provider.get_session_snapshot(key, default)
                    is_modified = current_value != snapshot
                    settings_dialog.widgets[ind_key].setVisible(is_modified)
            checkbox.stateChanged.connect(on_checkbox_changed)

        return checkbox

    def add_line_edit(
        self,
        parent_layout: QLayout,
        config_key: str,
        default_value: str = "",
        placeholder: Optional[str] = None,
        tooltip: Optional[str] = None
    ) -> QLineEdit:
        """
        添加文本框设置项

        Args:
            parent_layout: 父布局
            config_key: 配置键名
            default_value: 默认值
            placeholder: 占位文本
            tooltip: 提示文本

        Returns:
            创建的 QLineEdit 实例
        """
        line_edit = QLineEdit()
        line_edit.setText(self.tab.config.get(config_key, default_value))
        if placeholder:
            line_edit.setPlaceholderText(placeholder)
        if tooltip:
            line_edit.setToolTip(tooltip)

        self._create_setting_row(parent_layout, config_key, line_edit)
        self.tab.widgets[config_key] = line_edit

        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            indicator_key = f"{config_key}_modified"
            def on_text_changed(text, key=config_key, default=default_value, ind_key=indicator_key):
                from core.config_provider import config_provider
                config_provider.set(key, text, emit_event=False)
                if ind_key in settings_dialog.widgets:
                    snapshot = config_provider.get_session_snapshot(key, default)
                    is_modified = text != snapshot
                    settings_dialog.widgets[ind_key].setVisible(is_modified)
            line_edit.textChanged.connect(on_text_changed)

        return line_edit

    def add_spinbox(
        self,
        parent_layout: QLayout,
        config_key: str,
        default_value: int = 0,
        min_value: int = 0,
        max_value: int = 100,
        tooltip: Optional[str] = None
    ) -> QSpinBox:
        """
        添加数值框设置项

        Args:
            parent_layout: 父布局
            config_key: 配置键名
            default_value: 默认值
            min_value: 最小值
            max_value: 最大值
            tooltip: 提示文本

        Returns:
            创建的 QSpinBox 实例
        """
        spinbox = QSpinBox()
        spinbox.setRange(min_value, max_value)
        spinbox.setValue(self.tab.config.get(config_key, default_value))
        if tooltip:
            spinbox.setToolTip(tooltip)

        self._create_setting_row(parent_layout, config_key, spinbox)
        self.tab.widgets[config_key] = spinbox

        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            indicator_key = f"{config_key}_modified"
            def on_value_changed(value, key=config_key, default=default_value, ind_key=indicator_key):
                from core.config_provider import config_provider
                config_provider.set(key, value, emit_event=False)
                if ind_key in settings_dialog.widgets:
                    snapshot = config_provider.get_session_snapshot(key, default)
                    is_modified = value != snapshot
                    settings_dialog.widgets[ind_key].setVisible(is_modified)
            spinbox.valueChanged.connect(on_value_changed)

        return spinbox

    def add_combobox(
        self,
        parent_layout: QLayout,
        config_key: str,
        items: list[tuple[str, Any]],
        default_value: Any = None,
        tooltip: Optional[str] = None
    ) -> QComboBox:
        """
        添加下拉框设置项

        Args:
            parent_layout: 父布局
            config_key: 配置键名
            items: 选项列表 [(显示文本, 数据值), ...]
            default_value: 默认值
            tooltip: 提示文本

        Returns:
            创建的 QComboBox 实例
        """
        combobox = QComboBox()
        for text, data in items:
            combobox.addItem(text, data)

        # 设置当前值
        current_value = self.tab.config.get(config_key, default_value)
        if current_value is not None:
            index = combobox.findData(current_value)
            if index >= 0:
                combobox.setCurrentIndex(index)

        if tooltip:
            combobox.setToolTip(tooltip)

        self._create_setting_row(parent_layout, config_key, combobox)
        self.tab.widgets[config_key] = combobox

        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            indicator_key = f"{config_key}_modified"
            def on_index_changed(index, key=config_key, cb=combobox, default=default_value, ind_key=indicator_key):
                from core.config_provider import config_provider
                value = cb.itemData(index)
                config_provider.set(key, value, emit_event=False)
                if ind_key in settings_dialog.widgets:
                    snapshot = config_provider.get_session_snapshot(key, default)
                    is_modified = value != snapshot
                    settings_dialog.widgets[ind_key].setVisible(is_modified)
            combobox.currentIndexChanged.connect(on_index_changed)

        return combobox

    def add_custom_widget(
        self,
        parent_layout: QLayout,
        config_key: str,
        widget: QWidget,
        signal_name: str,
        value_getter: Callable[[], Any],
        default_value: Any = None
    ) -> QWidget:
        """
        添加自定义控件设置项

        Args:
            parent_layout: 父布局
            config_key: 配置键名
            widget: 自定义控件实例
            signal_name: 信号名称（如 'valueChanged'）
            value_getter: 获取当前值的函数
            default_value: 默认值

        Returns:
            传入的控件实例
        """
        self._create_setting_row(parent_layout, config_key, widget)
        self.tab.widgets[config_key] = widget

        settings_dialog = self._get_settings_dialog()
        if settings_dialog and hasattr(widget, signal_name):
            signal = getattr(widget, signal_name)
            signal.connect(
                lambda *args, key=config_key, getter=value_getter, default=default_value: settings_dialog._on_setting_changed(
                    key, getter(), default
                )
            )

        return widget

    def _create_setting_row(
        self,
        parent_layout: QLayout,
        config_key: str,
        widget: QWidget
    ) -> QHBoxLayout:
        """
        创建设置行（控件 + 星形指示器）

        Args:
            parent_layout: 父布局
            config_key: 配置键名
            widget: 设置控件

        Returns:
            创建的水平布局
        """
        layout = QHBoxLayout()
        layout.addWidget(widget)

        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            layout.addWidget(settings_dialog._create_modified_indicator(config_key))

        # 支持 QFormLayout（使用 addRow）和普通布局（使用 addLayout）
        if isinstance(parent_layout, QFormLayout):
            parent_layout.addRow(layout)
        else:
            parent_layout.addLayout(layout)
        return layout

    def add_row_to_form_layout(
        self,
        form_layout: QFormLayout,
        label: str,
        config_key: str,
        widget: QWidget
    ) -> None:
        """
        向 QFormLayout 添加带标签和星形指示器的行

        Args:
            form_layout: 表单布局
            label: 标签文本
            config_key: 配置键名
            widget: 设置控件
        """
        layout = QHBoxLayout()
        layout.addWidget(widget)

        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            layout.addWidget(settings_dialog._create_modified_indicator(config_key))

        form_layout.addRow(label, layout)

    def add_checkbox_to_form_layout(
        self,
        form_layout: QFormLayout,
        label: str,
        config_key: str,
        checkbox_text: str,
        default_value: bool = False,
        tooltip: Optional[str] = None
    ) -> QCheckBox:
        """
        向 QFormLayout 添加带星形指示器的复选框

        Args:
            form_layout: 表单布局
            label: 标签文本（可以为空字符串）
            config_key: 配置键名
            checkbox_text: 复选框显示文本
            default_value: 默认值
            tooltip: 提示文本

        Returns:
            创建的 QCheckBox 实例
        """
        checkbox = QCheckBox(checkbox_text)
        checkbox.setChecked(self.tab.config.get(config_key, default_value))
        if tooltip:
            checkbox.setToolTip(tooltip)

        layout = QHBoxLayout()
        layout.addWidget(checkbox)

        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            indicator_key = f"{config_key}_modified"
            indicator = settings_dialog._create_modified_indicator(config_key)
            layout.addWidget(indicator)

            def on_checkbox_changed(state, key=config_key, default=default_value, ind_key=indicator_key):
                current_value = (state == Qt.CheckState.Checked) or (state == 2)
                from core.config_provider import config_provider
                config_provider.set(key, current_value, emit_event=False)
                if ind_key in settings_dialog.widgets:
                    snapshot = config_provider.get_session_snapshot(key, default)
                    is_modified = current_value != snapshot
                    settings_dialog.widgets[ind_key].setVisible(is_modified)
            checkbox.stateChanged.connect(on_checkbox_changed)

        form_layout.addRow(label, layout)
        self.tab.widgets[config_key] = checkbox

        return checkbox
