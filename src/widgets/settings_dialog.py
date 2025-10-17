from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, 
                               QSpinBox, QLabel, QPushButton, QComboBox, QFormLayout,
                               QTabWidget, QWidget, QScrollArea, QFrame, QLineEdit,
                               QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import os
import json

class SettingsDialog(QDialog):
    # 定义信号，当设置改变时发出
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.parent = parent
        self.config_manager = config_manager
        self.config = config_manager.config if config_manager else {}
        
        self.setWindowTitle(self.tr("设置"))
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
        tab_widget.addTab(general_tab, self.tr("常规"))
        
        # 外观设置标签页
        display_tab = self._create_display_tab()
        tab_widget.addTab(display_tab, self.tr("外观"))
        
        # 高级设置标签页
        advanced_tab = self._create_advanced_tab()
        tab_widget.addTab(advanced_tab, self.tr("高级"))
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_ok = QPushButton(self.tr("确定"))
        self.btn_cancel = QPushButton(self.tr("取消"))
        self.btn_apply = QPushButton(self.tr("应用"))
        
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_apply.clicked.connect(self.apply_settings)
        
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        button_layout.addWidget(self.btn_apply)
        
        layout.addLayout(button_layout)
        
    def _create_general_tab(self):
        """创建常规设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # 文件操作组
        file_group = QGroupBox(self.tr("文件操作"))
        file_layout = QFormLayout(file_group)
        
        # 显示隐藏文件
        self.chk_show_hidden = QCheckBox(self.tr("显示隐藏文件"))
        file_layout.addRow(self.chk_show_hidden)
        
        # 显示文件夹大小
        self.chk_show_all_sizes = QCheckBox(self.tr("显示文件夹大小"))
        file_layout.addRow(self.chk_show_all_sizes)
        
        layout.addWidget(file_group)
        
        # 搜索组
        search_group = QGroupBox(self.tr("搜索"))
        search_layout = QFormLayout(search_group)
        
        # 搜索时包含隐藏文件
        self.chk_search_hidden = QCheckBox(self.tr("搜索时包含隐藏文件"))
        search_layout.addRow(self.chk_search_hidden)
        
        layout.addWidget(search_group)
        
        # 路径组
        path_group = QGroupBox(self.tr("路径"))
        path_layout = QFormLayout(path_group)
        
        # 记住上次路径
        self.chk_remember_path = QCheckBox(self.tr("记住上次路径"))
        path_layout.addRow(self.chk_remember_path)
        
        layout.addWidget(path_group)
        layout.addStretch()
        
        # 存储控件引用
        self.widgets.update({
            'show_hidden': self.chk_show_hidden,
            'show_all_sizes': self.chk_show_all_sizes,
            'search_hidden': self.chk_search_hidden,
            'remember_path': self.chk_remember_path
        })
        
        return widget
        
    def _create_display_tab(self):
        """创建显示设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # 界面显示组
        interface_group = QGroupBox(self.tr("界面显示"))
        interface_layout = QFormLayout(interface_group)
        
        # 显示修改时间
        self.chk_show_mtime = QCheckBox(self.tr("显示修改时间"))
        interface_layout.addRow(self.chk_show_mtime)
        
        # 图标大小
        self.spin_icon_size = QSpinBox()
        self.spin_icon_size.setRange(16, 128)
        self.spin_icon_size.setSingleStep(8)
        interface_layout.addRow(self.tr("图标大小:"), self.spin_icon_size)
        
        # 文件列表字体大小
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(8, 24)
        self.spin_font_size.setSingleStep(1)
        interface_layout.addRow(self.tr("字体大小:"), self.spin_font_size)
        
        layout.addWidget(interface_group)
        
        # 语言组
        language_group = QGroupBox(self.tr("语言"))
        language_layout = QHBoxLayout(language_group)
        
        self.combo_language = QComboBox()
        self.combo_language.addItem(self.tr("简体中文"), "zh_CN")
        self.combo_language.addItem(self.tr("English"), "en")
        language_layout.addWidget(self.combo_language)
        
        layout.addWidget(language_group)
        
        # 主题组
        theme_group = QGroupBox(self.tr("主题"))
        theme_layout = QHBoxLayout(theme_group)
        
        self.combo_theme = QComboBox()
        self.combo_theme.addItem(self.tr("浅色"), "light")
        self.combo_theme.addItem(self.tr("深色"), "dark")
        theme_layout.addWidget(self.combo_theme)
        
        layout.addWidget(theme_group)
        layout.addStretch()
        
        # 存储控件引用
        self.widgets.update({
            'show_mtime': self.chk_show_mtime,
            'icon_size': self.spin_icon_size,
            'font_size': self.spin_font_size,
            'language': self.combo_language,
            'theme': self.combo_theme
        })
        
        return widget
        
    def _create_advanced_tab(self):
        """创建高级设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # 数据库组
        db_group = QGroupBox(self.tr("数据库"))
        db_layout = QFormLayout(db_group)
        
        # 数据库路径
        db_path_layout = QHBoxLayout()
        self.line_db_path = QLineEdit()
        self.btn_browse_db = QPushButton(self.tr("浏览"))
        self.btn_browse_db.clicked.connect(self._browse_db_path)
        db_path_layout.addWidget(self.line_db_path)
        db_path_layout.addWidget(self.btn_browse_db)
        db_layout.addRow(self.tr("数据库路径:"), db_path_layout)
        
        layout.addWidget(db_group)
        
        # 缓存组
        cache_group = QGroupBox(self.tr("缓存"))
        cache_layout = QVBoxLayout(cache_group)
        
        self.chk_enable_cache = QCheckBox(self.tr("启用文件夹大小缓存"))
        cache_layout.addWidget(self.chk_enable_cache)
        
        # 缓存清理按钮
        cache_btn_layout = QHBoxLayout()
        self.btn_clean_cache = QPushButton(self.tr("清理缓存"))
        self.btn_clean_cache.clicked.connect(self._clean_cache)
        cache_btn_layout.addStretch()
        cache_btn_layout.addWidget(self.btn_clean_cache)
        cache_layout.addLayout(cache_btn_layout)
        
        layout.addWidget(cache_group)
        
        # 性能组
        performance_group = QGroupBox(self.tr("性能"))
        perf_layout = QFormLayout(performance_group)
        
        # 最大并发线程数
        self.spin_max_threads = QSpinBox()
        self.spin_max_threads.setRange(1, 50)
        self.spin_max_threads.setSingleStep(1)
        perf_layout.addRow(self.tr("最大并发线程数:"), self.spin_max_threads)
        
        layout.addWidget(performance_group)
        layout.addStretch()
        
        # 存储控件引用
        self.widgets.update({
            'db_path': self.line_db_path,
            'enable_cache': self.chk_enable_cache,
            'max_threads': self.spin_max_threads
        })
        
        return widget
        
    def _browse_db_path(self):
        """浏览数据库路径"""
        current_path = self.line_db_path.text()
        if not current_path:
            current_path = "./userdata/db/folder_size.db"
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("选择数据库文件"),
            current_path,
            self.tr("数据库文件 (*.db)")
        )
        
        if file_path:
            self.line_db_path.setText(file_path)
            
    def _clean_cache(self):
        """清理缓存"""
        reply = QMessageBox.question(
            self,
            self.tr("确认"),
            self.tr("确定要清理所有缓存吗？"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 这里应该调用实际的缓存清理逻辑
            QMessageBox.information(self, self.tr("提示"), self.tr("缓存已清理"))
            
    def _load_settings(self):
        """加载设置"""
        # 常规设置
        self.chk_show_hidden.setChecked(self.config.get("show_hidden", False))
        self.chk_show_all_sizes.setChecked(self.config.get("show_all_sizes", True))
        self.chk_search_hidden.setChecked(self.config.get("search_hidden", False))
        self.chk_remember_path.setChecked(self.config.get("remember_path", True))
        
        # 显示设置
        self.chk_show_mtime.setChecked(self.config.get("show_mtime", True))
        self.spin_icon_size.setValue(self.config.get("file_list_icon_size", 40))
        self.spin_font_size.setValue(self.config.get("font_size", 12))
        
        # 语言设置
        lang = self.config.get("language", "zh_CN")
        index = self.combo_language.findData(lang)
        if index >= 0:
            self.combo_language.setCurrentIndex(index)
            
        # 主题设置
        theme = self.config.get("theme", "light")
        index = self.combo_theme.findData(theme)
        if index >= 0:
            self.combo_theme.setCurrentIndex(index)
            
        # 高级设置
        self.line_db_path.setText(self.config.get("db_path", "./userdata/db/folder_size.db"))
        self.chk_enable_cache.setChecked(self.config.get("enable_cache", True))
        self.spin_max_threads.setValue(self.config.get("max_threads", 10))
        
    def _save_settings(self):
        """保存设置"""
        new_config = {
            # 常规设置
            "show_hidden": self.chk_show_hidden.isChecked(),
            "show_all_sizes": self.chk_show_all_sizes.isChecked(),
            "search_hidden": self.chk_search_hidden.isChecked(),
            "remember_path": self.chk_remember_path.isChecked(),
            
            # 显示设置
            "show_mtime": self.chk_show_mtime.isChecked(),
            "file_list_icon_size": self.spin_icon_size.value(),
            "font_size": self.spin_font_size.value(),
            
            # 语言设置
            "language": self.combo_language.currentData(),
            
            # 主题设置
            "theme": self.combo_theme.currentData(),
            
            # 高级设置
            "db_path": self.line_db_path.text(),
            "enable_cache": self.chk_enable_cache.isChecked(),
            "max_threads": self.spin_max_threads.value()
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
        
        QMessageBox.information(self, self.tr("提示"), self.tr("设置已应用"))
        
    def accept(self):
        """点击确定按钮"""
        self.apply_settings()
        super().accept()
        
    @staticmethod
    def show_settings_dialog(parent=None, config_manager=None):
        """静态方法显示设置对话框"""
        dialog = SettingsDialog(parent, config_manager)
        return dialog.exec()

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QMainWindow
    import sys
    
    class MockConfigManager:
        def __init__(self):
            self.config = {
                "show_hidden": False,
                "show_all_sizes": True,
                "search_hidden": False,
                "remember_path": True,
                "show_mtime": True,
                "file_list_icon_size": 40,
                "font_size": 12,
                "language": "zh_CN",
                "theme": "light",
                "db_path": "./userdata/db/folder_size.db",
                "enable_cache": True,
                "max_threads": 10
            }
            
        def save_config(self):
            print("配置已保存")
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = QMainWindow()
    main_window.setWindowTitle("设置窗口预览")
    main_window.resize(800, 600)
    
    # 创建配置管理器模拟对象
    config_manager = MockConfigManager()
    
    # 创建并显示设置对话框
    dialog = SettingsDialog(main_window, config_manager)
    dialog.show()
    
    sys.exit(app.exec())