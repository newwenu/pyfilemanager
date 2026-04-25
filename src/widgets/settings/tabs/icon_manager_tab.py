from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLabel, QCheckBox, QGroupBox, QScrollArea,
                               QPushButton, QMessageBox, QLineEdit, QGridLayout,
                               QFrame)
from PySide6.QtCore import Qt
import os
import json


class IconManagerTab(QWidget):
    """图标管理标签页 - 按扩展名设置"""

    def __init__(self, parent=None, config=None, widgets=None, translation=None):
        super().__init__(parent)
        self.config = config or {}
        self.widgets = widgets or {}
        self.translation = translation or {}
        self._icon_type_file = os.path.join("userdata", "file-icon_type", "file-icon_type.json")
        self._setup_ui()

    def _get_settings_dialog(self):
        """获取设置对话框实例"""
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, '_on_setting_changed'):
                return parent
            parent = parent.parent()
        return None

    def _get_all_extensions(self):
        """动态从 file-icon_type.json 和主配置获取所有扩展名"""
        extensions = set()

        # 1. 从 file-icon_type.json 读取扩展名
        if os.path.exists(self._icon_type_file):
            try:
                with open(self._icon_type_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    file_type_mapping = data.get("file_type_mapping", {})
                    for ext_list in file_type_mapping.values():
                        for ext in ext_list:
                            if ext and ext != "*":  # 排除空字符串和通配符
                                extensions.add(ext)
            except Exception as e:
                print(f"读取扩展名失败: {e}")

        # 2. 从主配置读取用户自定义的扩展名
        config_extensions = self._get_config_value()
        for ext in config_extensions:
            if ext and ext != "*":
                extensions.add(ext)

        # 如果读取失败，使用默认扩展名
        if not extensions:
            extensions = {
                ".exe", ".bat", ".cmd", ".msi", ".com",
                ".dll", ".lib", ".h", ".vhdx",
                ".txt", ".md", ".doc", ".docx",
                ".jpg", ".png", ".mp4", ".mp3",
                ".zip", ".pdf", ".py", ".js"
            }

        return sorted(extensions)

    def _get_config_value(self):
        """从主配置获取值"""
        return self.config.get("use_system_icons_for_extensions", [".exe", ".bat", ".cmd", ".msi", ".com", ".dll"])

    def _get_config_default(self):
        """从主配置获取default类型回退设置"""
        return self.config.get("use_system_icons_for_default", True)

    def _save_to_config(self, extensions=None, use_for_default=None):
        """保存到主配置"""
        settings_dialog = self._get_settings_dialog()
        if settings_dialog and settings_dialog.config_manager:
            if extensions is not None:
                settings_dialog.config_manager.config["use_system_icons_for_extensions"] = extensions
            if use_for_default is not None:
                settings_dialog.config_manager.config["use_system_icons_for_default"] = use_for_default
            settings_dialog.config_manager.save_config()

    def _setup_ui(self):
        """设置图标管理标签页UI"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 说明标签
        info_label = QLabel(
            self.translation.get(
                "lbl_icon_manager_info",
                "对以下扩展名的文件使用系统图标（Windows原生图标，较慢但更准确）："
            )
        )
        info_label.setWordWrap(True)
        scroll_layout.addWidget(info_label)

        # default类型回退选项组
        default_group = QGroupBox(
            self.translation.get("group_default_fallback", "默认类型回退")
        )
        default_layout = QHBoxLayout(default_group)

        self.default_checkbox = QCheckBox(
            self.translation.get("chk_use_system_for_default", "对default类型（无匹配扩展名）使用系统图标")
        )
        self.default_checkbox.setChecked(self._get_config_default())
        self.default_checkbox.stateChanged.connect(self._on_default_checkbox_changed)
        default_layout.addWidget(self.default_checkbox)

        # 将复选框添加到 widgets 字典（用于修改指示器循环）
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            settings_dialog.widgets['use_system_icons_for_default'] = self.default_checkbox
            default_layout.addWidget(settings_dialog._create_modified_indicator('use_system_icons_for_default'))
        default_layout.addStretch()

        scroll_layout.addWidget(default_group)

        # 获取当前配置值
        current_extensions = self._get_config_value()

        # 扩展名列表组
        ext_group = QGroupBox(
            self.translation.get("group_extensions", "扩展名列表（勾选使用系统图标）")
        )
        ext_layout = QVBoxLayout(ext_group)

        # 创建滚动区域用于多列显示
        scroll_area_ext = QScrollArea()
        scroll_area_ext.setWidgetResizable(True)
        scroll_content_ext = QWidget()
        self.ext_grid_layout = QGridLayout(scroll_content_ext)
        self.ext_grid_layout.setSpacing(5)

        # 加载所有扩展名并创建复选框
        all_extensions = self._get_all_extensions()

        # 多列显示（每行4列）
        columns = 4
        self._ext_checkboxes = {}

        for index, ext in enumerate(all_extensions):
            checkbox = QCheckBox(ext)
            checkbox.setChecked(ext in current_extensions)
            checkbox.stateChanged.connect(self._on_checkbox_changed)
            self._ext_checkboxes[ext] = checkbox

            row = index // columns
            col = index % columns
            self.ext_grid_layout.addWidget(checkbox, row, col)

        scroll_area_ext.setWidget(scroll_content_ext)
        ext_layout.addWidget(scroll_area_ext)

        # 添加自定义扩展名
        add_layout = QHBoxLayout()
        self.ext_input = QLineEdit()
        self.ext_input.setPlaceholderText(
            self.translation.get("ph_extension", ".ext")
        )
        add_layout.addWidget(self.ext_input)

        self.btn_add = QPushButton(
            self.translation.get("btn_add", "添加")
        )
        self.btn_add.clicked.connect(self._add_extension)
        add_layout.addWidget(self.btn_add)

        ext_layout.addLayout(add_layout)
        scroll_layout.addWidget(ext_group)

        # 按钮布局
        button_layout = QHBoxLayout()

        # 全选按钮
        self.btn_select_all = QPushButton(
            self.translation.get("btn_select_all", "全选")
        )
        self.btn_select_all.clicked.connect(self._select_all)
        button_layout.addWidget(self.btn_select_all)

        # 全不选按钮
        self.btn_deselect_all = QPushButton(
            self.translation.get("btn_deselect_all", "全不选")
        )
        self.btn_deselect_all.clicked.connect(self._deselect_all)
        button_layout.addWidget(self.btn_deselect_all)

        # 重置默认按钮
        self.btn_reset_default = QPushButton(
            self.translation.get("btn_reset_default", "重置默认")
        )
        self.btn_reset_default.clicked.connect(self._reset_default)
        button_layout.addWidget(self.btn_reset_default)

        button_layout.addStretch()
        scroll_layout.addLayout(button_layout)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def _on_checkbox_changed(self):
        """扩展名复选框状态变化时的处理"""
        selected_extensions = []
        for ext, checkbox in self._ext_checkboxes.items():
            if checkbox.isChecked():
                selected_extensions.append(ext)

        # 排序后比较
        selected_sorted = sorted(selected_extensions)

        # 保存到主配置
        self._save_to_config(extensions=selected_extensions)

        # 通知设置对话框（用于更新修改指示器和窗口标题）
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            # 获取默认值
            default_value = [".exe", ".bat", ".cmd", ".msi", ".com", ".dll"]
            settings_dialog._on_setting_changed(
                'use_system_icons_for_extensions', selected_sorted, default_value
            )

    def _on_default_checkbox_changed(self):
        """default类型回退复选框状态变化时的处理"""
        use_for_default = self.default_checkbox.isChecked()

        # 保存到主配置
        self._save_to_config(use_for_default=use_for_default)

        # 通知设置对话框
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            settings_dialog._on_setting_changed(
                'use_system_icons_for_default', use_for_default, False
            )

    def _add_extension(self):
        """添加自定义扩展名"""
        ext = self.ext_input.text().strip().lower()
        if not ext:
            return

        # 自动处理：确保以点开头，去除多余空格和特殊字符
        ext = ext.replace(' ', '')  # 去除空格
        if not ext.startswith('.'):
            ext = '.' + ext

        # 验证扩展名格式（只允许字母、数字、点、下划线、连字符）
        import re
        if not re.match(r'^[.][a-zA-Z0-9._-]+$', ext):
            QMessageBox.warning(
                self,
                self.translation.get("msg_warning_title", "警告"),
                self.translation.get("msg_invalid_extension", "无效的扩展名格式")
            )
            return

        # 检查是否已存在
        if ext in self._ext_checkboxes:
            # 已存在，选中它
            self._ext_checkboxes[ext].setChecked(True)
            self.ext_input.clear()
            return

        # 添加新复选框
        checkbox = QCheckBox(ext)
        checkbox.setChecked(True)
        checkbox.stateChanged.connect(self._on_checkbox_changed)
        self._ext_checkboxes[ext] = checkbox

        # 计算位置并添加到网格
        columns = 4
        index = len(self._ext_checkboxes) - 1
        row = index // columns
        col = index % columns
        self.ext_grid_layout.addWidget(checkbox, row, col)

        self.ext_input.clear()

    def _select_all(self):
        """全选所有扩展名"""
        for checkbox in self._ext_checkboxes.values():
            checkbox.setChecked(True)

    def _deselect_all(self):
        """全不选所有扩展名"""
        for checkbox in self._ext_checkboxes.values():
            checkbox.setChecked(False)

    def _reset_default(self):
        """重置为默认设置"""
        reply = QMessageBox.question(
            self,
            self.translation.get("msg_confirm_title", "确认"),
            self.translation.get("msg_reset_confirm", "确定要重置为默认设置吗？"),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            default_list = [".exe", ".bat", ".cmd", ".msi", ".com", ".dll"]

            # 保存到主配置
            self._save_to_config(extensions=default_list, use_for_default=False)

            # 更新扩展名复选框状态
            for ext, checkbox in self._ext_checkboxes.items():
                checkbox.setChecked(ext in default_list)

            # 更新default回退复选框
            self.default_checkbox.setChecked(False)

            # 通知设置对话框（重置后无修改）
            settings_dialog = self._get_settings_dialog()
            if settings_dialog:
                settings_dialog._on_setting_changed(
                    'use_system_icons_for_extensions', sorted(default_list), sorted(default_list)
                )
                settings_dialog._on_setting_changed(
                    'use_system_icons_for_default', False, False
                )

    def save_settings(self):
        """保存所有设置（供外部调用）"""
        selected_extensions = []
        for ext, checkbox in self._ext_checkboxes.items():
            if checkbox.isChecked():
                selected_extensions.append(ext)

        use_for_default = self.default_checkbox.isChecked()
        self._save_to_config(extensions=selected_extensions, use_for_default=use_for_default)
        return {
            "use_system_icons_for_extensions": selected_extensions,
            "use_system_icons_for_default": use_for_default
        }

    def get_use_system_icons_extensions(self):
        """获取使用系统图标的扩展名列表"""
        return self._get_config_value()

    def get_use_system_icons_for_default(self):
        """获取default类型是否使用系统图标"""
        return self.default_checkbox.isChecked()
