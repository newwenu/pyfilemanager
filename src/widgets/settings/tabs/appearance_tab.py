from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLabel, QLineEdit, QCheckBox, QSpinBox,
                               QPushButton, QGroupBox, QComboBox, QScrollArea)
from PySide6.QtCore import Qt
import os
from src.widgets.collapsible_section import CollapsibleSection
from src.widgets.settings.value_slider import IconSizeSlider, FontSizeSlider
from src.widgets.settings.setting_item_group import SettingItemGroup

class AppearanceTab(QWidget):
    """外观设置标签页"""

    def __init__(self, parent=None, config=None, widgets=None, translation=None):
        super().__init__(parent)
        self.config = config or {}
        self.widgets = widgets or {}
        self.translation = translation or {}
        self._items = SettingItemGroup(self)
        self._setup_ui()

    def _get_settings_dialog(self):
        """获取设置对话框实例

        由于AppearanceTab是嵌套在QTabWidget中的，self.parent()返回的是QStackedWidget，
        需要通过多层parent()调用才能获取到真正的SettingsDialog实例
        """
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, '_on_setting_changed'):
                return parent
            parent = parent.parent()
        return None

    def _create_setting_row(self, widget, config_key, label_text=None):
        """创建设置行（通用方法）- 使用 SettingItemGroup

        Args:
            widget: 设置控件
            config_key: 配置键名
            label_text: 标签文本（可选）

        Returns:
            tuple: (layout, widget) 或 (label, layout, widget)
        """
        layout = QHBoxLayout()
        layout.addWidget(widget, stretch=1)

        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            layout.addWidget(settings_dialog._create_modified_indicator(config_key))

        self.widgets[config_key] = widget

        if label_text:
            return label_text, layout, widget
        return layout, widget

    def _create_icon_size_slider(self, config_key, default_val=40, label=""):
        """创建图标大小滑块"""
        slider = IconSizeSlider(
            default_val=self.config.get(config_key, default_val),
            label=label
        )
        return slider

    def _create_font_size_slider(self, config_key, default_val=15, label=""):
        """创建字体大小滑块"""
        slider = FontSizeSlider(
            default_val=self.config.get(config_key, default_val),
            label=label
        )
        return slider

    def _setup_ui(self):
        """设置外观标签页UI"""
        # 创建带滚动区域的布局
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 窗口设置组
        window_group = QGroupBox(self.translation.get("group_window", "窗口设置"))
        window_layout = QFormLayout(window_group)

        # 窗口标题
        self.window_title_edit = QLineEdit()
        self.window_title_edit.setText(self.config.get("window_title", "极简文件管理器"))
        self._items.add_row_to_form_layout(
            window_layout,
            self.translation.get("lbl_window_title", "窗口标题:"),
            'window_title',
            self.window_title_edit
        )
        self.widgets['window_title'] = self.window_title_edit

        # 显示状态栏
        self.statusbar_checkbox = self._items.add_checkbox_to_form_layout(
            window_layout, "", 'statusbar_visible',
            self.translation.get("chk_show_statusbar", "显示状态栏"),
            default_value=True
        )

        window_group.setLayout(window_layout)
        scroll_layout.addWidget(window_group)

        # 背景设置子组
        background_group = QGroupBox(self.translation.get("group_background", "背景设置"))
        background_layout = QFormLayout(background_group)
        background_layout.setSpacing(10)

        # 背景图片
        self.background_image_edit = QLineEdit()
        self.background_image_edit.setText(self.config.get("background_image", ""))
        self._items.add_row_to_form_layout(
            background_layout,
            self.translation.get("lbl_background_path", "背景图片"),
            'background_image',
            self.background_image_edit
        )
        self.widgets['background_image'] = self.background_image_edit

        # 浏览按钮
        self.btn_browse_bg = QPushButton(self.translation.get("btn_browse", "浏览..."))
        background_layout.addRow(self.btn_browse_bg)

        scroll_layout.addWidget(background_group)

        # 可折叠的显示设置栏目
        display_section = CollapsibleSection(self.translation.get("group_display_settings", "显示设置（点击展开）"))
        display_layout = QVBoxLayout()
        display_layout.setSpacing(10)

        # 界面显示子组
        interface_group = QGroupBox(self.translation.get("group_interface", "界面显示"))
        interface_layout = QFormLayout(interface_group)
        interface_layout.setSpacing(10)

        # 图标大小（使用滑块替代 SpinBox）
        self.icon_size_slider = self._create_icon_size_slider(
            'file_list_icon_size', 40,
            self.translation.get("lbl_icon_size", "图标大小")
        )
        layout, _ = self._create_setting_row(self.icon_size_slider, 'file_list_icon_size')
        interface_layout.addRow(layout)

        # 字体大小（使用滑块替代 SpinBox）
        self.font_size_slider = self._create_font_size_slider(
            'font_size', 15,
            self.translation.get("lbl_font_size", "字体大小")
        )
        layout, _ = self._create_setting_row(self.font_size_slider, 'font_size')
        interface_layout.addRow(layout)

        # 字体族
        self.font_family_edit = QLineEdit()
        self.font_family_edit.setText(self.config.get("font_family", "Segoe UI"))
        self._items.add_row_to_form_layout(
            interface_layout,
            self.translation.get("lbl_font_family", "字体族"),
            'font_family',
            self.font_family_edit
        )
        self.widgets['font_family'] = self.font_family_edit

        display_layout.addWidget(interface_group)

        # 导航树设置子组
        tree_group = QGroupBox(self.translation.get("group_nav_tree", "导航树设置"))
        tree_layout = QFormLayout(tree_group)
        tree_layout.setSpacing(10)

        # 导航树图标大小（使用滑块替代 SpinBox）
        self.tree_icon_size_slider = self._create_icon_size_slider(
            'nav_tree_icon_size', 60,
            self.translation.get("lbl_nav_tree_icon_size", "导航树图标大小")
        )
        layout, _ = self._create_setting_row(self.tree_icon_size_slider, 'nav_tree_icon_size')
        tree_layout.addRow(layout)

        # 导航树字体大小（使用滑块替代 SpinBox）
        self.tree_font_size_slider = self._create_font_size_slider(
            'nav_tree_font_size', 15,
            self.translation.get("lbl_nav_tree_font_size", "导航树字体大小")
        )
        layout, _ = self._create_setting_row(self.tree_font_size_slider, 'nav_tree_font_size')
        tree_layout.addRow(layout)

        display_layout.addWidget(tree_group)

        # 驱动器设置子组
        drive_group = QGroupBox(self.translation.get("group_drives", "驱动器设置"))
        drive_layout = QFormLayout(drive_group)
        drive_layout.setSpacing(10)

        # 驱动器图标大小（使用滑块替代 SpinBox）
        self.drive_icon_size_slider = self._create_icon_size_slider(
            'drive_icon_size', 60,
            self.translation.get("lbl_drive_icon_size", "驱动器图标大小")
        )
        layout, _ = self._create_setting_row(self.drive_icon_size_slider, 'drive_icon_size')
        drive_layout.addRow(layout)

        # 驱动器字体大小（使用滑块替代 SpinBox）
        self.drive_font_size_slider = self._create_font_size_slider(
            'drive_font_size', 13,
            self.translation.get("lbl_drive_font_size", "驱动器字体大小")
        )
        layout, _ = self._create_setting_row(self.drive_font_size_slider, 'drive_font_size')
        drive_layout.addRow(layout)

        display_layout.addWidget(drive_group)

        # 设置显示设置栏目内容
        display_section.setContentLayout(display_layout)
        scroll_layout.addWidget(display_section)

        # 语言设置组
        language_group = QGroupBox(self.translation.get("group_language", "语言"))
        language_layout = QHBoxLayout(language_group)

        self.language_combo = self._create_language_combo()
        language_h_layout = QHBoxLayout()
        language_h_layout.addWidget(self.language_combo)
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            language_h_layout.addWidget(settings_dialog._create_modified_indicator('language'))
        language_h_layout.setContentsMargins(0, 0, 0, 0)
        language_layout.addLayout(language_h_layout)
        scroll_layout.addWidget(language_group)
        self.widgets['language'] = self.language_combo

        # 主题设置组
        theme_group = QGroupBox(self.translation.get("group_theme", "主题"))
        theme_layout = QHBoxLayout(theme_group)

        self.theme_combo = self._create_theme_combo()
        theme_h_layout = QHBoxLayout()
        theme_h_layout.addWidget(self.theme_combo)
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            theme_h_layout.addWidget(settings_dialog._create_modified_indicator('theme'))
        theme_h_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.addLayout(theme_h_layout)
        scroll_layout.addWidget(theme_group)
        self.widgets['theme'] = self.theme_combo

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

        # 延迟连接信号，确保所有控件都已创建
        self._connect_signals()

    def _connect_signals(self):
        """连接信号"""
        # 获取设置对话框实例
        settings_dialog = self._get_settings_dialog()

        if settings_dialog:
            # 文本框信号
            self.window_title_edit.textChanged.connect(
                lambda text: settings_dialog._on_setting_changed('window_title', text))
            self.background_image_edit.textChanged.connect(
                lambda text: settings_dialog._on_setting_changed('background_image', text))
            self.font_family_edit.textChanged.connect(
                lambda text: settings_dialog._on_setting_changed('font_family', text))

            # 复选框信号
            self.statusbar_checkbox.stateChanged.connect(
                lambda state: settings_dialog._on_setting_changed('statusbar_visible', state == Qt.CheckState.Checked))
            # 滑块信号
            self.icon_size_slider.valueChanged.connect(
                lambda value: settings_dialog._on_setting_changed('file_list_icon_size', value))
            self.font_size_slider.valueChanged.connect(
                lambda value: settings_dialog._on_setting_changed('font_size', value))
            self.tree_icon_size_slider.valueChanged.connect(
                lambda value: settings_dialog._on_setting_changed('nav_tree_icon_size', value))
            self.tree_font_size_slider.valueChanged.connect(
                lambda value: settings_dialog._on_setting_changed('nav_tree_font_size', value))
            self.drive_icon_size_slider.valueChanged.connect(
                lambda value: settings_dialog._on_setting_changed('drive_icon_size', value))
            self.drive_font_size_slider.valueChanged.connect(
                lambda value: settings_dialog._on_setting_changed('drive_font_size', value))

            # 下拉框信号
            self.language_combo.currentIndexChanged.connect(
                lambda index: settings_dialog._on_setting_changed('language', self.language_combo.itemData(index)))
            self.theme_combo.currentIndexChanged.connect(
                lambda index: settings_dialog._on_setting_changed('theme', self.theme_combo.itemData(index)))

        # 按钮信号
        self.btn_browse_bg.clicked.connect(self._browse_background_image)

    def _browse_background_image(self):
        """浏览背景图片"""
        current_path = self.background_image_edit.text() or os.getcwd()
        file_filter = "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*.*)"
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            file_path = settings_dialog._browse_file(current_path, "选择背景图片", file_filter)
        else:
            file_path = None
        if file_path:
            self.background_image_edit.setText(file_path)

    def _create_language_combo(self):
        """创建语言选择下拉框"""
        combo = QComboBox()
        # 添加语言选项 - 使用与配置文件中一致的值
        combo.addItem(self.translation.get("opt_chinese", "简体中文"), "zh_CN")
        combo.addItem(self.translation.get("opt_english", "English"), "en_US")
        # 设置当前选中项
        current_lang = self.config.get("language", "zh_CN")
        index = combo.findData(current_lang)
        if index >= 0:
            combo.setCurrentIndex(index)
        return combo

    def _create_theme_combo(self):
        """创建主题选择下拉框"""
        combo = QComboBox()
        # 添加主题选项
        combo.addItem(self.translation.get("opt_auto_theme", "自动"), "auto")
        combo.addItem(self.translation.get("opt_light_theme", "浅色"), "light")
        combo.addItem(self.translation.get("opt_dark_theme", "深色"), "dark")
        # 设置当前选中项
        current_theme = self.config.get("theme", "auto")
        index = combo.findData(current_theme)
        if index >= 0:
            combo.setCurrentIndex(index)
        return combo
