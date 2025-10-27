from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLabel, QLineEdit, QCheckBox, QSpinBox, 
                               QPushButton, QGroupBox, QScrollArea, QComboBox)
from PySide6.QtCore import Qt

class AdvancedTab(QWidget):
    """高级设置标签页"""
    
    def __init__(self, parent=None, config=None, widgets=None, translation=None):
        super().__init__(parent)
        self.config = config or {}
        self.widgets = widgets or {}
        self.translation = translation or {}
        self._setup_ui()
        self._connect_signals()
    
    def _get_settings_dialog(self):
        """获取设置对话框实例"""
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, '_create_modified_indicator') and hasattr(parent, '_on_setting_changed'):
                return parent
            parent = parent.parent()
        return None
        
    def _setup_ui(self):
        """设置高级标签页UI"""
        # 创建带滚动区域的布局
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 日志设置组
        log_group = QGroupBox(self.translation.get("group_log", "日志设置"))
        log_layout = QFormLayout(log_group)
        
        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem(self.translation.get("opt_debug", "调试 (DEBUG)"), "DEBUG")
        self.log_level_combo.addItem(self.translation.get("opt_info", "信息 (INFO)"), "INFO")
        self.log_level_combo.addItem(self.translation.get("opt_warning", "警告 (WARNING)"), "WARNING")
        self.log_level_combo.addItem(self.translation.get("opt_error", "错误 (ERROR)"), "ERROR")
        self.log_level_combo.addItem(self.translation.get("opt_critical", "严重 (CRITICAL)"), "CRITICAL")
        current_log_level = self.config.get("log_level", "INFO").upper()
        index = self.log_level_combo.findData(current_log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
        log_level_layout = QHBoxLayout()
        log_level_layout.addWidget(self.log_level_combo)
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            log_level_layout.addWidget(settings_dialog._create_modified_indicator('log_level'))
        log_level_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.addRow(QLabel(self.translation.get("lbl_log_level", "日志级别:")), log_level_layout)
        self.widgets['log_level'] = self.log_level_combo
        
        log_group.setLayout(log_layout)
        scroll_layout.addWidget(log_group)
        
        # 数据库设置组
        db_group = QGroupBox(self.translation.get("group_database", "数据库设置"))
        db_layout = QFormLayout(db_group)
        
        # 数据库路径
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setText(self.config.get("db_path", "./userdata/db/folder_size.db"))
        self.btn_browse_db = QPushButton(self.translation.get("btn_browse", "浏览"))
        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(self.db_path_edit)
        db_path_layout.addWidget(self.btn_browse_db)
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            db_path_layout.addWidget(settings_dialog._create_modified_indicator('db_path'))
        db_path_layout.setContentsMargins(0, 0, 0, 0)
        db_layout.addRow(QLabel(self.translation.get("lbl_db_path", "数据库路径:")), db_path_layout)
        self.widgets['db_path'] = self.db_path_edit
        
        db_group.setLayout(db_layout)
        scroll_layout.addWidget(db_group)
        
        # 缓存设置组
        cache_group = QGroupBox(self.translation.get("group_cache", "缓存设置"))
        cache_layout = QVBoxLayout(cache_group)
        
        # 启用缓存
        self.enable_cache_checkbox = QCheckBox(self.translation.get("chk_enable_cache", "启用文件夹大小缓存"))
        self.enable_cache_checkbox.setChecked(self.config.get("enable_cache", True))
        enable_cache_layout = QHBoxLayout()
        enable_cache_layout.addWidget(self.enable_cache_checkbox)
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            enable_cache_layout.addWidget(settings_dialog._create_modified_indicator('enable_cache'))
        enable_cache_layout.setContentsMargins(0, 0, 0, 0)
        cache_layout.addLayout(enable_cache_layout)
        self.widgets['enable_cache'] = self.enable_cache_checkbox
        
        # 清理缓存按钮
        self.btn_clean_cache = QPushButton(self.translation.get("btn_clean_cache", "清理缓存"))
        cache_btn_layout = QHBoxLayout()
        cache_btn_layout.addStretch()
        cache_btn_layout.addWidget(self.btn_clean_cache)
        cache_layout.addLayout(cache_btn_layout)
        
        cache_group.setLayout(cache_layout)
        scroll_layout.addWidget(cache_group)
        
        # 性能设置组
        perf_group = QGroupBox(self.translation.get("group_performance", "性能设置"))
        perf_layout = QFormLayout(perf_group)
        
        # 最大并发线程数
        self.max_threads_spinbox = QSpinBox()
        self.max_threads_spinbox.setRange(1, 50)
        self.max_threads_spinbox.setSingleStep(1)
        self.max_threads_spinbox.setValue(self.config.get("max_threads", 10))
        max_threads_layout = QHBoxLayout()
        max_threads_layout.addWidget(self.max_threads_spinbox)
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            max_threads_layout.addWidget(settings_dialog._create_modified_indicator('max_threads'))
        max_threads_layout.setContentsMargins(0, 0, 0, 0)
        perf_layout.addRow(QLabel(self.translation.get("lbl_max_threads", "最大并发线程数:")), max_threads_layout)
        self.widgets['max_threads'] = self.max_threads_spinbox
        
        perf_group.setLayout(perf_layout)
        scroll_layout.addWidget(perf_group)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
    
    def _connect_signals(self):
        """连接信号"""
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            # 下拉框信号
            self.log_level_combo.currentIndexChanged.connect(
                lambda index: settings_dialog._on_setting_changed('log_level', self.log_level_combo.itemData(index), "INFO"))
            
            # 文本框信号
            self.db_path_edit.textChanged.connect(
                lambda text: settings_dialog._on_setting_changed('db_path', text, "./userdata/db/folder_size.db"))
            
            # 复选框信号
            self.enable_cache_checkbox.stateChanged.connect(
                lambda state: settings_dialog._on_setting_changed('enable_cache', state == Qt.CheckState.Checked, True))
            
            # 数值框信号
            self.max_threads_spinbox.valueChanged.connect(
                lambda value: settings_dialog._on_setting_changed('max_threads', value, 10))
        
        # 按钮信号
        self.btn_browse_db.clicked.connect(self._browse_db_path)
        self.btn_clean_cache.clicked.connect(self._clean_cache)
    
    def _browse_db_path(self):
        """浏览数据库路径"""
        current_path = self.db_path_edit.text()
        if not current_path:
            current_path = "./userdata/db/folder_size.db"
            
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择数据库文件",
            current_path,
            "数据库文件 (*.db)"
        )
        
        if file_path:
            self.db_path_edit.setText(file_path)
    
    def _clean_cache(self):
        """清理缓存"""
        from PySide6.QtWidgets import QMessageBox
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