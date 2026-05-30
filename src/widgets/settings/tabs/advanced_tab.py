from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLabel, QLineEdit, QCheckBox, QSpinBox,
                               QPushButton, QGroupBox, QScrollArea)
from src.widgets.settings.setting_item_group import SettingItemGroup


class AdvancedTab(QWidget):
    """高级设置标签页"""
    
    def __init__(self, parent=None, config=None, widgets=None, translation=None):
        super().__init__(parent)
        self.config = config or {}
        self.widgets = widgets or {}
        self.translation = translation or {}
        self._items = SettingItemGroup(self)
        self._setup_ui()
    
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
        log_level_items = [
            (self.translation.get("opt_debug", "调试 (DEBUG)"), "DEBUG"),
            (self.translation.get("opt_info", "信息 (INFO)"), "INFO"),
            (self.translation.get("opt_warning", "警告 (WARNING)"), "WARNING"),
            (self.translation.get("opt_error", "错误 (ERROR)"), "ERROR"),
            (self.translation.get("opt_critical", "严重 (CRITICAL)"), "CRITICAL"),
        ]
        from PySide6.QtWidgets import QComboBox
        self.log_level_combo = QComboBox()
        for text, data in log_level_items:
            self.log_level_combo.addItem(text, data)
        current_log_level = self.config.get("log_level", "INFO").upper()
        index = self.log_level_combo.findData(current_log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
        self._items.add_row_to_form_layout(
            log_layout,
            self.translation.get("lbl_log_level", "日志级别:"),
            'log_level',
            self.log_level_combo
        )
        self.widgets['log_level'] = self.log_level_combo

        # 连接下拉框信号
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            indicator_key = 'log_level_modified'
            def on_log_level_changed(index, sd=settings_dialog, ind_key=indicator_key):
                from core.config_provider import config_provider
                value = self.log_level_combo.itemData(index)
                config_provider.set('log_level', value, emit_event=False)
                if ind_key in sd.widgets:
                    snapshot = config_provider.get_session_snapshot('log_level', 'INFO')
                    is_modified = value != snapshot
                    sd.widgets[ind_key].setVisible(is_modified)
            self.log_level_combo.currentIndexChanged.connect(on_log_level_changed)

        log_group.setLayout(log_layout)
        scroll_layout.addWidget(log_group)
        
        # 数据库设置组
        db_group = QGroupBox(self.translation.get("group_database", "数据库设置"))
        db_layout = QFormLayout(db_group)
        
        # 数据库路径
        self.db_path_edit = self._items.add_line_edit(
            db_layout, 'db_path',
            default_value="./userdata/db/folder_size.db"
        )
        self.btn_browse_db = QPushButton(self.translation.get("btn_browse", "浏览"))
        
        db_group.setLayout(db_layout)
        scroll_layout.addWidget(db_group)
        
        # 缓存设置组
        cache_group = QGroupBox(self.translation.get("group_cache", "缓存设置"))
        cache_layout = QVBoxLayout(cache_group)
        
        # 启用缓存
        self.enable_cache_checkbox = self._items.add_checkbox(
            cache_layout, 'enable_cache',
            self.translation.get("chk_enable_cache", "启用文件夹大小缓存"),
            default_value=True
        )
        
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
        self.max_threads_spinbox = self._items.add_spinbox(
            perf_layout, 'max_threads',
            default_value=10,
            min_value=1,
            max_value=50
        )
        
        perf_group.setLayout(perf_layout)
        scroll_layout.addWidget(perf_group)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        
        # 连接信号
        self.btn_browse_db.clicked.connect(self._browse_db_path)
        self.btn_clean_cache.clicked.connect(self._clean_cache)

    def _get_settings_dialog(self):
        """获取设置对话框实例"""
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, '_create_modified_indicator'):
                return parent
            parent = parent.parent()
        return None
    
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
