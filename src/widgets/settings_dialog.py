from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, 
                               QSpinBox, QPushButton, QComboBox, QFormLayout,
                               QTabWidget, QWidget, QScrollArea, QLineEdit, QLabel,
                               QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal
import os
from widgets.collapsible_section import CollapsibleSection

class SettingsDialog(QDialog):
    # 定义信号，当设置改变时发出
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None, config_manager=None, language_manager=None):
        super().__init__(parent)
        self.parent = parent
        self.config_manager = config_manager
        self.language_manager = language_manager
        self.config = config_manager.config if config_manager else {}
        
        # 获取设置组件的翻译字典
        self.translation = language_manager.get_component_translation("settings") if language_manager else {}
        
        self.setWindowTitle(self.translation.get("dialog_title", "设置"))
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        
        # 存储控件引用以便后续访问
        self.widgets = {}
        
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        
        # 创建标签页
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # 常规设置标签页
        general_tab = self._create_general_tab()
        tab_widget.addTab(general_tab, self.translation.get("tab_general", "常规"))
        
        # 外观设置标签页
        appearance_tab = self._create_appearance_tab()
        tab_widget.addTab(appearance_tab, self.translation.get("tab_appearance", "外观"))
        
        # 高级设置标签页
        advanced_tab = self._create_advanced_tab()
        tab_widget.addTab(advanced_tab, self.translation.get("tab_advanced", "高级"))
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_ok = QPushButton(self.translation.get("btn_ok", "确定"))
        self.btn_cancel = QPushButton(self.translation.get("btn_cancel", "取消"))
        self.btn_apply = QPushButton(self.translation.get("btn_apply", "应用"))
        
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_apply.clicked.connect(self.apply_settings)
        
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        button_layout.addWidget(self.btn_apply)
        
        layout.addLayout(button_layout)
        
    def _create_modified_indicator(self, name):
        """创建修改状态指示器（星号标签）"""
        label = QLabel("*")
        label.setStyleSheet("color: red; font-weight: bold;")
        label.setVisible(False)  # 默认隐藏
        label.setFixedWidth(20)  # 设置固定宽度避免界面错乱
        # 将修改状态指示器存储到widgets字典中
        self.widgets[f'{name}_modified'] = label
        return label
    
    def _connect_modified_signal(self, widget, config_key, default_value=None):
        """连接控件的修改信号到统一的处理函数"""
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(lambda text, key=config_key, default=default_value: self._on_setting_changed(key, text, default))
        elif isinstance(widget, QCheckBox):
            widget.stateChanged.connect(lambda state, key=config_key, default=default_value: self._on_setting_changed(key, bool(state), default))
        elif isinstance(widget, QSpinBox):
            widget.valueChanged.connect(lambda value, key=config_key, default=default_value: self._on_setting_changed(key, value, default))
        elif isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(lambda index, key=config_key, default=default_value, widget=widget: self._on_setting_changed(key, widget.currentData() if widget.currentData() is not None else widget.currentText(), default))
    
    def _on_setting_changed(self, config_key, current_value, default_value):
        """统一处理设置项变化的函数"""
        # 获取对应的修改状态指示器
        modified_indicator_key = f"{config_key}_modified"
        if modified_indicator_key in self.widgets:
            # 获取配置文件中保存的值
            config_value = self.config.get(config_key, default_value)
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
        print(f"Setting {config_key} changed to {current_value} (config: {self.config.get(config_key, default_value)})")
    
    def _create_general_tab(self):
        """创建常规设置标签页"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 创建内容widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        
        # 文件操作组
        file_group = QGroupBox(self.translation.get("group_file_operations", "文件操作"))
        file_layout = QVBoxLayout(file_group)
        
        # 显示隐藏文件
        self.chk_show_hidden = QCheckBox(self.translation.get("chk_show_hidden", "显示隐藏文件和文件夹"))
        lbl_show_hidden_modified = self._create_modified_indicator("show_hidden_files")
        lbl_show_hidden_modified.setFixedWidth(20)  # 固定星号标签宽度
        show_hidden_layout = QHBoxLayout()
        show_hidden_layout.addWidget(self.chk_show_hidden)
        show_hidden_layout.addWidget(lbl_show_hidden_modified)
        show_hidden_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.addLayout(show_hidden_layout)
        
        # 显示所有文件大小
        self.chk_show_all_sizes = QCheckBox(self.translation.get("chk_show_all_sizes", "显示所有文件大小"))
        # self.chk_show_all_sizes.setToolTip(self.translation.get("tip_show_all_sizes", "如果未勾选，小于1KB的文件将显示为0KB"))
        lbl_show_all_sizes_modified = self._create_modified_indicator("show_all_sizes")
        lbl_show_all_sizes_modified.setFixedWidth(20)  # 固定星号标签宽度
        show_all_sizes_layout = QHBoxLayout()
        show_all_sizes_layout.addWidget(self.chk_show_all_sizes)
        show_all_sizes_layout.addWidget(lbl_show_all_sizes_modified)
        show_all_sizes_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.addLayout(show_all_sizes_layout)
        
        layout.addWidget(file_group)
        
        # 搜索组
        search_group = QGroupBox(self.translation.get("group_search", "搜索"))
        search_layout = QVBoxLayout(search_group)
        
        # 搜索时包含隐藏文件
        self.chk_search_hidden = QCheckBox(self.translation.get("chk_search_hidden", "搜索时包含隐藏文件"))
        lbl_search_hidden_modified = self._create_modified_indicator("search_hidden")
        lbl_search_hidden_modified.setFixedWidth(20)  # 固定星号标签宽度
        search_hidden_layout = QHBoxLayout()
        search_hidden_layout.addWidget(self.chk_search_hidden)
        search_hidden_layout.addWidget(lbl_search_hidden_modified)
        search_hidden_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.addLayout(search_hidden_layout)
        
        layout.addWidget(search_group)
        
        # 路径组
        path_group = QGroupBox(self.translation.get("group_path", "路径"))
        path_layout = QVBoxLayout(path_group)
        
        # 启动时随机显示图片
        self.chk_start_random = QCheckBox(self.translation.get("chk_start_random", "启动时随机显示图片"))
        lbl_start_random_modified = self._create_modified_indicator("start_random")
        lbl_start_random_modified.setFixedWidth(20)  # 固定星号标签宽度
        start_random_layout = QHBoxLayout()
        start_random_layout.addWidget(self.chk_start_random)
        start_random_layout.addWidget(lbl_start_random_modified)
        start_random_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.addLayout(start_random_layout)
        
        layout.addWidget(path_group)
        layout.addStretch()
        
        # 将内容widget设置到滚动区域
        scroll_area.setWidget(content_widget)
        
        # 存储控件引用
        self.widgets.update({
            'show_hidden_files': self.chk_show_hidden,
            'show_all_sizes': self.chk_show_all_sizes,
            'search_hidden': self.chk_search_hidden,
            'start_random': self.chk_start_random
        })
        
        return scroll_area
        
    def _create_appearance_tab(self):
        """创建显示设置标签页"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 创建内容widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        
        # 窗口设置组
        window_group = QGroupBox(self.translation.get("group_window", "窗口设置"))
        window_layout = QFormLayout(window_group)
        
        # 窗口标题
        self.line_window_title = QLineEdit()
        lbl_window_title_modified = self._create_modified_indicator("window_title")
        window_title_layout = QHBoxLayout()
        window_title_layout.addWidget(self.line_window_title)
        window_title_layout.addWidget(lbl_window_title_modified)
        window_title_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.addRow(self.translation.get("lbl_window_title", "窗口标题:"), window_title_layout)
        
        # 显示状态栏
        self.chk_statusbar_visible = QCheckBox(self.translation.get("chk_show_statusbar", "显示状态栏"))
        lbl_statusbar_visible_modified = self._create_modified_indicator("statusbar_visible")
        statusbar_layout = QHBoxLayout()
        statusbar_layout.addWidget(self.chk_statusbar_visible)
        statusbar_layout.addWidget(lbl_statusbar_visible_modified)
        statusbar_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.addRow("", statusbar_layout)
        
        layout.addWidget(window_group)
        
        # 背景图片设置组（移到折叠区域外）
        background_group = QGroupBox(self.translation.get("group_background", "背景图片"))
        background_layout = QFormLayout(background_group)
        
        # 背景图片路径
        bg_layout = QHBoxLayout()
        self.line_background_image = QLineEdit()
        self.lbl_background_image_modified = self._create_modified_indicator("background_image")
        self.lbl_background_image_modified.setFixedWidth(20)  # 固定星号标签宽度
        self.btn_browse_bg = QPushButton(self.translation.get("btn_browse", "浏览"))
        self.btn_browse_bg.clicked.connect(self._browse_background_image)
        bg_layout.addWidget(self.line_background_image)
        bg_layout.addWidget(self.lbl_background_image_modified)
        bg_layout.addWidget(self.btn_browse_bg)
        background_layout.addRow(self.translation.get("lbl_background_path", "背景图片路径:"), bg_layout)
        
        layout.addWidget(background_group)
        
        # 显示设置可折叠栏目（包含界面显示、导航树设置和驱动器设置）
        display_section = CollapsibleSection(self.translation.get("group_display_settings", "显示设置（点击展开）"))
        
        # 创建显示设置的内容布局
        display_layout = QVBoxLayout()
        display_layout.setSpacing(10)
        
        # 界面显示组
        interface_group = QGroupBox(self.translation.get("group_interface", "界面显示"))
        interface_layout = QFormLayout(interface_group)
        
        # 显示修改时间
        self.chk_show_mtime = QCheckBox(self.translation.get("chk_show_mtime", "显示修改时间"))
        lbl_show_mtime_modified = self._create_modified_indicator("show_mtime")
        lbl_show_mtime_modified.setFixedWidth(20)  # 固定星号标签宽度
        show_mtime_layout = QHBoxLayout()
        show_mtime_layout.addWidget(self.chk_show_mtime)
        show_mtime_layout.addWidget(lbl_show_mtime_modified)
        show_mtime_layout.setContentsMargins(0, 0, 0, 0)
        interface_layout.addRow("", show_mtime_layout)
        
        # 图标大小
        self.spin_icon_size = QSpinBox()
        self.spin_icon_size.setRange(16, 128)
        self.spin_icon_size.setSingleStep(8)
        lbl_icon_size_modified = self._create_modified_indicator("icon_size")
        lbl_icon_size_modified.setFixedWidth(20)  # 固定星号标签宽度
        icon_size_layout = QHBoxLayout()
        icon_size_layout.addWidget(self.spin_icon_size)
        icon_size_layout.addWidget(lbl_icon_size_modified)
        icon_size_layout.setContentsMargins(0, 0, 0, 0)
        interface_layout.addRow(self.translation.get("lbl_icon_size", "图标大小:"), icon_size_layout)
        
        # 文件列表字体大小
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(8, 24)
        self.spin_font_size.setSingleStep(1)
        lbl_font_size_modified = self._create_modified_indicator("font_size")
        lbl_font_size_modified.setFixedWidth(20)  # 固定星号标签宽度
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(self.spin_font_size)
        font_size_layout.addWidget(lbl_font_size_modified)
        font_size_layout.setContentsMargins(0, 0, 0, 0)
        interface_layout.addRow(self.translation.get("lbl_font_size", "字体大小:"), font_size_layout)
        
        # 字体族
        self.line_font_family = QLineEdit()
        self.lbl_font_family_modified = self._create_modified_indicator("font_family")
        self.lbl_font_family_modified.setFixedWidth(20)  # 固定星号标签宽度
        
        # 创建水平布局容纳输入框和星号标签
        font_family_layout = QHBoxLayout()
        font_family_layout.addWidget(self.line_font_family)
        font_family_layout.addWidget(self.lbl_font_family_modified)
        font_family_layout.setContentsMargins(0, 0, 0, 0)
        
        interface_layout.addRow(self.translation.get("lbl_font_family", "字体族:"), font_family_layout)
        
        display_layout.addWidget(interface_group)
        
        # 导航树设置组
        nav_tree_group = QGroupBox(self.translation.get("group_nav_tree", "导航树设置"))
        nav_tree_layout = QFormLayout(nav_tree_group)
        
        # 导航树图标大小
        self.spin_nav_tree_icon_size = QSpinBox()
        self.spin_nav_tree_icon_size.setRange(16, 128)
        self.spin_nav_tree_icon_size.setSingleStep(8)
        lbl_nav_tree_icon_size_modified = self._create_modified_indicator("nav_tree_icon_size")
        nav_tree_icon_size_layout = QHBoxLayout()
        nav_tree_icon_size_layout.addWidget(self.spin_nav_tree_icon_size)
        nav_tree_icon_size_layout.addWidget(lbl_nav_tree_icon_size_modified)
        nav_tree_icon_size_layout.setContentsMargins(0, 0, 0, 0)
        nav_tree_layout.addRow(self.translation.get("lbl_nav_tree_icon_size", "图标大小:"), nav_tree_icon_size_layout)
        
        # 导航树字体大小
        self.spin_nav_tree_font_size = QSpinBox()
        self.spin_nav_tree_font_size.setRange(8, 24)
        self.spin_nav_tree_font_size.setSingleStep(1)
        lbl_nav_tree_font_size_modified = self._create_modified_indicator("nav_tree_font_size")
        nav_tree_font_size_layout = QHBoxLayout()
        nav_tree_font_size_layout.addWidget(self.spin_nav_tree_font_size)
        nav_tree_font_size_layout.addWidget(lbl_nav_tree_font_size_modified)
        nav_tree_font_size_layout.setContentsMargins(0, 0, 0, 0)
        nav_tree_layout.addRow(self.translation.get("lbl_nav_tree_font_size", "字体大小:"), nav_tree_font_size_layout)
        
        display_layout.addWidget(nav_tree_group)
        
        # 驱动器设置组
        drive_group = QGroupBox(self.translation.get("group_drives", "驱动器设置"))
        drive_layout = QFormLayout(drive_group)
        
        # 驱动器图标大小
        self.spin_drive_icon_size = QSpinBox()
        self.spin_drive_icon_size.setRange(16, 128)
        self.spin_drive_icon_size.setSingleStep(8)
        lbl_drive_icon_size_modified = self._create_modified_indicator("drive_icon_size")
        drive_icon_size_layout = QHBoxLayout()
        drive_icon_size_layout.addWidget(self.spin_drive_icon_size)
        drive_icon_size_layout.addWidget(lbl_drive_icon_size_modified)
        drive_icon_size_layout.setContentsMargins(0, 0, 0, 0)
        drive_layout.addRow(self.translation.get("lbl_drive_icon_size", "图标大小:"), drive_icon_size_layout)
        
        # 驱动器字体大小
        self.spin_drive_font_size = QSpinBox()
        self.spin_drive_font_size.setRange(8, 24)
        self.spin_drive_font_size.setSingleStep(1)
        lbl_drive_font_size_modified = self._create_modified_indicator("drive_font_size")
        drive_font_size_layout = QHBoxLayout()
        drive_font_size_layout.addWidget(self.spin_drive_font_size)
        drive_font_size_layout.addWidget(lbl_drive_font_size_modified)
        drive_font_size_layout.setContentsMargins(0, 0, 0, 0)
        drive_layout.addRow(self.translation.get("lbl_drive_font_size", "字体大小:"), drive_font_size_layout)
        
        display_layout.addWidget(drive_group)
        
        # 设置显示设置栏目内容
        display_section.setContentLayout(display_layout)
        layout.addWidget(display_section)
        
        # 语言组
        language_group = QGroupBox(self.translation.get("group_language", "语言"))
        language_layout = QHBoxLayout(language_group)
        
        self.combo_language = QComboBox()
        self.combo_language.addItem(self.translation.get("opt_chinese", "简体中文"), "zh_CN")
        self.combo_language.addItem(self.translation.get("opt_english", "English"), "en")
        lbl_language_modified = self._create_modified_indicator("language")
        language_h_layout = QHBoxLayout()
        language_h_layout.addWidget(self.combo_language)
        language_h_layout.addWidget(lbl_language_modified)
        language_h_layout.setContentsMargins(0, 0, 0, 0)
        language_layout.addLayout(language_h_layout)
        
        layout.addWidget(language_group)
        
        # 主题组
        theme_group = QGroupBox(self.translation.get("group_theme", "主题"))
        theme_layout = QHBoxLayout(theme_group)
        
        self.combo_theme = QComboBox()
        self.combo_theme.addItem(self.translation.get("opt_light_theme", "浅色"), "light")
        self.combo_theme.addItem(self.translation.get("opt_dark_theme", "深色"), "dark")
        lbl_theme_modified = self._create_modified_indicator("theme")
        theme_h_layout = QHBoxLayout()
        theme_h_layout.addWidget(self.combo_theme)
        theme_h_layout.addWidget(lbl_theme_modified)
        theme_h_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.addLayout(theme_h_layout)
        
        layout.addWidget(theme_group)
        layout.addStretch()
        
        # 将内容widget设置到滚动区域
        scroll_area.setWidget(content_widget)
        
        # 存储控件引用
        self.widgets.update({
            'window_title': self.line_window_title,
            'statusbar_visible': self.chk_statusbar_visible,
            'show_mtime': self.chk_show_mtime,
            'background_image': self.line_background_image,
            'icon_size': self.spin_icon_size,
            'font_size': self.spin_font_size,
            'font_family': self.line_font_family,
            'nav_tree_icon_size': self.spin_nav_tree_icon_size,
            'nav_tree_font_size': self.spin_nav_tree_font_size,
            'drive_icon_size': self.spin_drive_icon_size,
            'drive_font_size': self.spin_drive_font_size,
            'language': self.combo_language,
            'theme': self.combo_theme
        })

        return scroll_area
        
    def _create_advanced_tab(self):
        """创建高级设置标签页"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 创建内容widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        
        # 日志组
        log_group = QGroupBox(self.translation.get("group_logging", "日志"))
        log_layout = QFormLayout(log_group)
        
        # 日志级别
        self.combo_log_level = QComboBox()
        self.combo_log_level.addItem(self.translation.get("opt_debug", "调试 (DEBUG)"), "DEBUG")
        self.combo_log_level.addItem(self.translation.get("opt_info", "信息 (INFO)"), "INFO")
        self.combo_log_level.addItem(self.translation.get("opt_warning", "警告 (WARNING)"), "WARNING")
        self.combo_log_level.addItem(self.translation.get("opt_error", "错误 (ERROR)"), "ERROR")
        self.combo_log_level.addItem(self.translation.get("opt_critical", "严重 (CRITICAL)"), "CRITICAL")
        lbl_log_level_modified = self._create_modified_indicator("log_level")
        log_level_layout = QHBoxLayout()
        log_level_layout.addWidget(self.combo_log_level)
        log_level_layout.addWidget(lbl_log_level_modified)
        log_level_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.addRow(self.translation.get("lbl_log_level", "日志级别:"), log_level_layout)
        
        layout.addWidget(log_group)
        
        # 数据库组
        db_group = QGroupBox(self.translation.get("group_database", "数据库"))
        db_layout = QFormLayout(db_group)
        
        # 数据库路径
        self.line_db_path = QLineEdit()
        lbl_db_path_modified = self._create_modified_indicator("db_path")
        lbl_db_path_modified.setFixedWidth(20)  # 固定星号标签宽度
        self.btn_browse_db = QPushButton(self.translation.get("btn_browse", "浏览"))
        self.btn_browse_db.clicked.connect(self._browse_db_path)
        db_path_h_layout = QHBoxLayout()
        db_path_h_layout.addWidget(self.line_db_path)
        db_path_h_layout.addWidget(lbl_db_path_modified)
        db_path_h_layout.addWidget(self.btn_browse_db)
        db_path_h_layout.setContentsMargins(0, 0, 0, 0)
        db_layout.addRow(self.translation.get("lbl_db_path", "数据库路径:"), db_path_h_layout)
        
        layout.addWidget(db_group)
        
        # 缓存组
        cache_group = QGroupBox(self.translation.get("group_cache", "缓存"))
        cache_layout = QVBoxLayout(cache_group)
        
        self.chk_enable_cache = QCheckBox(self.translation.get("chk_enable_cache", "启用文件夹大小缓存"))
        cache_layout.addWidget(self.chk_enable_cache)
        
        # 缓存清理按钮
        self.btn_clean_cache = QPushButton(self.translation.get("btn_clean_cache", "清理缓存"))
        self.btn_clean_cache.clicked.connect(self._clean_cache)
        lbl_enable_cache_modified = self._create_modified_indicator("enable_cache")
        enable_cache_layout = QHBoxLayout()
        enable_cache_layout.addWidget(self.chk_enable_cache)
        enable_cache_layout.addWidget(lbl_enable_cache_modified)
        enable_cache_layout.setContentsMargins(0, 0, 0, 0)
        cache_layout.addLayout(enable_cache_layout)
        
        cache_btn_layout = QHBoxLayout()
        cache_btn_layout.addStretch()
        cache_btn_layout.addWidget(self.btn_clean_cache)
        cache_layout.addLayout(cache_btn_layout)
        
        layout.addWidget(cache_group)
        
        # 性能组
        performance_group = QGroupBox(self.translation.get("group_performance", "性能"))
        perf_layout = QFormLayout(performance_group)
        
        # 最大并发线程数
        self.spin_max_threads = QSpinBox()
        self.spin_max_threads.setRange(1, 50)
        self.spin_max_threads.setSingleStep(1)
        lbl_max_threads_modified = self._create_modified_indicator("max_threads")
        max_threads_layout = QHBoxLayout()
        max_threads_layout.addWidget(self.spin_max_threads)
        max_threads_layout.addWidget(lbl_max_threads_modified)
        max_threads_layout.setContentsMargins(0, 0, 0, 0)
        perf_layout.addRow(self.translation.get("lbl_max_threads", "最大并发线程数:"), max_threads_layout)
        
        layout.addWidget(performance_group)
        layout.addStretch()
        
        # 将内容widget设置到滚动区域
        scroll_area.setWidget(content_widget)
        
        # 存储控件引用
        self.widgets.update({
            'log_level': self.combo_log_level,
            'db_path': self.line_db_path,
            'enable_cache': self.chk_enable_cache,
            'max_threads': self.spin_max_threads
        })
        
        return scroll_area
        
    def _browse_db_path(self):
        """浏览数据库路径"""
        current_path = self.line_db_path.text()
        if not current_path:
            current_path = "./userdata/db/folder_size.db"
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择数据库文件",
            current_path,
            "数据库文件 (*.db)"
        )
        
        if file_path:
            self.line_db_path.setText(file_path)
            
    def _clean_cache(self):
        """清理缓存"""
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要清理所有缓存吗？这将删除所有文件夹大小缓存(注意:此操作不可逆)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 这里应该调用实际的缓存清理逻辑
            QMessageBox.information(self, "提示", "缓存已清理")
            
    def _browse_background_image(self):
        """浏览背景图片路径"""
        current_path = self.line_background_image.text()
        if not current_path:
            current_path = "./media/background.png"
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.translation.get("dlg_select_bg", "选择背景图片"),
            current_path,
            self.translation.get("dlg_image_files", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*)")
        )
        
        if file_path:
            self.line_background_image.setText(file_path)
            
    def _load_settings(self):
        """加载设置"""
        # 常规设置
        self.chk_show_hidden.setChecked(self.config.get("show_hidden_files", False))
        self._connect_modified_signal(self.chk_show_hidden, "show_hidden_files", False)
        self._on_setting_changed("show_hidden_files", self.config.get("show_hidden_files", False), False)

        self.chk_show_all_sizes.setChecked(self.config.get("show_all_sizes", False))
        self._connect_modified_signal(self.chk_show_all_sizes, "show_all_sizes", False)
        self._on_setting_changed("show_all_sizes", self.config.get("show_all_sizes", False), False)
        
        self.chk_search_hidden.setChecked(self.config.get("search_hidden", False))
        self._connect_modified_signal(self.chk_search_hidden, "search_hidden", False)
        self._on_setting_changed("search_hidden", self.config.get("search_hidden", False), False)
        
        self.chk_start_random.setChecked(self.config.get("start-random", False))
        self._connect_modified_signal(self.chk_start_random, "start-random", False)
        self._on_setting_changed("start-random", self.config.get("start-random", False), False)
        
        # 窗口设置
        self.line_window_title.setText(self.config.get("window_title", "极简文件管理器"))
        self._connect_modified_signal(self.line_window_title, "window_title", "极简文件管理器")
        self._on_setting_changed("window_title", self.config.get("window_title", "极简文件管理器"), "极简文件管理器")
        
        self.chk_statusbar_visible.setChecked(self.config.get("statusbar_visible", True))
        self._connect_modified_signal(self.chk_statusbar_visible, "statusbar_visible", True)
        self._on_setting_changed("statusbar_visible", self.config.get("statusbar_visible", True), True)
        
        # 显示设置
        self.chk_show_mtime.setChecked(self.config.get("show_mtime", False))
        self._connect_modified_signal(self.chk_show_mtime, "show_mtime", False)
        self._on_setting_changed("show_mtime", self.config.get("show_mtime", False), False)
        
        self.line_background_image.setText(self.config.get("background_image", "media/background.png"))
        self._connect_modified_signal(self.line_background_image, "background_image", "media/background.png")
        self._on_setting_changed("background_image", self.config.get("background_image", "media/background.png"), "media/background.png")
        
        self.spin_icon_size.setValue(self.config.get("file_list_icon_size", 40))
        self._connect_modified_signal(self.spin_icon_size, "icon_size", 40)
        self._on_setting_changed("icon_size", self.config.get("file_list_icon_size", 40), 40)
        
        self.spin_font_size.setValue(self.config.get("font_size", 15))
        self._connect_modified_signal(self.spin_font_size, "font_size", 15)
        self._on_setting_changed("font_size", self.config.get("font_size", 15), 15)
        
        self.line_font_family.setText(self.config.get("font_family", "Microsoft YaHei"))
        self._connect_modified_signal(self.line_font_family, "font_family", "Microsoft YaHei")
        self._on_setting_changed("font_family", self.config.get("font_family", "Microsoft YaHei"), "Microsoft YaHei")
        
        # 导航树设置
        self.spin_nav_tree_icon_size.setValue(self.config.get("nav_tree_icon_size", 60))
        self._connect_modified_signal(self.spin_nav_tree_icon_size, "nav_tree_icon_size", 60)
        self._on_setting_changed("nav_tree_icon_size", self.config.get("nav_tree_icon_size", 60), 60)
        
        self.spin_nav_tree_font_size.setValue(self.config.get("nav_tree_font_size", 15))
        self._connect_modified_signal(self.spin_nav_tree_font_size, "nav_tree_font_size", 15)
        self._on_setting_changed("nav_tree_font_size", self.config.get("nav_tree_font_size", 15), 15)
        
        # 驱动器设置
        self.spin_drive_icon_size.setValue(self.config.get("drive_icon_size", 60))
        self._connect_modified_signal(self.spin_drive_icon_size, "drive_icon_size", 60)
        self._on_setting_changed("drive_icon_size", self.config.get("drive_icon_size", 60), 60)
        
        self.spin_drive_font_size.setValue(self.config.get("drive_font_size", 13))
        self._connect_modified_signal(self.spin_drive_font_size, "drive_font_size", 13)
        self._on_setting_changed("drive_font_size", self.config.get("drive_font_size", 13), 13)
        
        # 语言设置
        lang = self.config.get("language", "zh_CN")
        index = self.combo_language.findData(lang)
        if index >= 0:
            self.combo_language.setCurrentIndex(index)
        self._connect_modified_signal(self.combo_language, "language", "zh_CN")
        self._on_setting_changed("language", lang, "zh_CN")
        
        # 主题设置
        theme = self.config.get("theme", "light")
        index = self.combo_theme.findData(theme)
        if index >= 0:
            self.combo_theme.setCurrentIndex(index)
        self._connect_modified_signal(self.combo_theme, "theme", "light")
        self._on_setting_changed("theme", theme, "light")
        
        # 高级设置
        # 日志级别
        log_level = self.config.get("log_level", "INFO").upper()
        index = self.combo_log_level.findData(log_level)
        if index >= 0:
            self.combo_log_level.setCurrentIndex(index)
        self._connect_modified_signal(self.combo_log_level, "log_level", "INFO")
        self._on_setting_changed("log_level", log_level, "INFO")
        
        self.line_db_path.setText(self.config.get("db_path", "./userdata/db/folder_size.db"))
        self._connect_modified_signal(self.line_db_path, "db_path", "./userdata/db/folder_size.db")
        self._on_setting_changed("db_path", self.config.get("db_path", "./userdata/db/folder_size.db"), "./userdata/db/folder_size.db")
        
        self.chk_enable_cache.setChecked(self.config.get("enable_cache", True))
        self._connect_modified_signal(self.chk_enable_cache, "enable_cache", True)
        self._on_setting_changed("enable_cache", self.config.get("enable_cache", True), True)
        
        self.spin_max_threads.setValue(self.config.get("max_threads", 10))
        self._connect_modified_signal(self.spin_max_threads, "max_threads", 10)
        self._on_setting_changed("max_threads", self.config.get("max_threads", 10), 10)
    def _save_settings(self):
        """保存设置"""
        new_config = {
            # 按照配置文件中定义的顺序保存配置项
            "window_title": self.line_window_title.text(),
            "initial_size": self.config.get("initial_size", [900, 600]),
            "file_list_bg_alpha": self.config.get("file_list_bg_alpha", 100),
            "nav_tree_bg_alpha": self.config.get("nav_tree_bg_alpha", 100),
            "background_image": self.line_background_image.text(),
            "background_alpha": self.config.get("background_alpha", 150),
            "font_size": self.spin_font_size.value(),
            "font_family": self.line_font_family.text(),
            "nav_tree_icon_size": self.spin_nav_tree_icon_size.value(),
            "file_list_icon_size": self.spin_icon_size.value(),
            "drive_icon_size": self.spin_drive_icon_size.value(),
            "file_list_font_size": self.spin_font_size.value(),
            "nav_tree_font_size": self.spin_nav_tree_font_size.value(),
            "drive_font_size": self.spin_drive_font_size.value(),
            "show_hidden_files": self.chk_show_hidden.isChecked(),
            "show_all_sizes": self.chk_show_all_sizes.isChecked(),
            "statusbar_visible": self.chk_statusbar_visible.isChecked(),
            "language": self.combo_language.currentData() or "zh_CN",
            "start_path": self.config.get("start_path", os.path.expanduser('~')),
            "log_level": self.combo_log_level.currentData().lower() or "info",
            "start-random": self.chk_start_random.isChecked(),
            "show_mtime": self.chk_show_mtime.isChecked()
        }
        
        return new_config
        
    def apply_settings(self):
        """应用设置"""
        new_config = self._save_settings()
        
        # 如果有配置管理器，则保存配置
        if self.config_manager:
            self.config_manager.config.update(new_config)
            self.config_manager.save_config()
            
        # 发出设置改变信号
        self.settings_changed.emit(new_config)
        
        # 使用状态栏显示设置已应用提示，而不是QMessageBox
        if self.parent and hasattr(self.parent, 'statusBar'):
            self.parent.statusBar().showMessage(self.translation.get("dlg_settings_applied", "设置已应用"), 2000)  # 显示3秒
        
    def accept(self):
        """点击确定按钮"""
        self.apply_settings()
        super().accept()