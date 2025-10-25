from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLabel, QLineEdit, QCheckBox, QSpinBox, 
                               QPushButton, QGroupBox, QScrollArea)
from PySide6.QtCore import Qt
import os

class GeneralTab(QWidget):
    """常规设置标签页"""
    
    def __init__(self, parent=None, config=None, widgets=None, translation=None):
        super().__init__(parent)
        self.config = config or {}
        self.widgets = widgets or {}
        self.translation = translation or {}
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """设置常规标签页UI"""
        # 创建带滚动区域的布局
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 文件操作组
        file_group = QGroupBox(self.translation.get("group_file_operations", "文件操作"))
        file_layout = QVBoxLayout(file_group)
        
        # 获取设置对话框实例用于创建修改指示器
        settings_dialog = self._get_settings_dialog()
        
        # 显示隐藏文件
        self.chk_show_hidden = QCheckBox(self.translation.get("chk_show_hidden", "显示隐藏文件和文件夹"))
        self.chk_show_hidden.setChecked(self.config.get("show_hidden_files", True))
        show_hidden_layout = QHBoxLayout()
        show_hidden_layout.addWidget(self.chk_show_hidden)
        if settings_dialog:
            show_hidden_layout.addWidget(settings_dialog._create_modified_indicator('show_hidden_files'))
        file_layout.addLayout(show_hidden_layout)
        self.widgets['show_hidden_files'] = self.chk_show_hidden
        
        # 显示所有文件夹大小
        self.chk_show_all_sizes = QCheckBox(self.translation.get("chk_show_folder_sizes", "显示所有文件夹大小"))
        self.chk_show_all_sizes.setChecked(self.config.get("show_all_sizes", False))
        show_all_sizes_layout = QHBoxLayout()
        show_all_sizes_layout.addWidget(self.chk_show_all_sizes)
        if settings_dialog:
            show_all_sizes_layout.addWidget(settings_dialog._create_modified_indicator('show_all_sizes'))
        file_layout.addLayout(show_all_sizes_layout)
        self.widgets['show_all_sizes'] = self.chk_show_all_sizes
        
        file_group.setLayout(file_layout)
        scroll_layout.addWidget(file_group)
        
        # # 基本设置组
        # basic_group = QGroupBox(self.translation.get("basic_settings", "基本设置"))
        # basic_layout = QFormLayout(basic_group)
        
        # basic_group.setLayout(basic_layout)
        # scroll_layout.addWidget(basic_group)
        
        # 搜索组
        search_group = QGroupBox(self.translation.get("group_search", "搜索"))
        search_layout = QVBoxLayout(search_group)
        
        # 搜索时包含隐藏文件
        self.chk_search_hidden = QCheckBox(self.translation.get("chk_search_hidden", "搜索时包含隐藏文件"))
        self.chk_search_hidden.setChecked(self.config.get("search_hidden", False))
        search_hidden_layout = QHBoxLayout()
        search_hidden_layout.addWidget(self.chk_search_hidden)
        if settings_dialog:
            search_hidden_layout.addWidget(settings_dialog._create_modified_indicator('search_hidden'))
        search_layout.addLayout(search_hidden_layout)
        self.widgets['search_hidden'] = self.chk_search_hidden
        
        search_group.setLayout(search_layout)
        scroll_layout.addWidget(search_group)
        
        # 路径组
        path_group = QGroupBox(self.translation.get("group_path", "路径"))
        path_layout = QVBoxLayout(path_group)
        
        # 启动时随机显示图片
        self.chk_start_random = QCheckBox(self.translation.get("chk_start_random_bg", "启动时随机显示图片"))
        self.chk_start_random.setChecked(self.config.get("start_random", False))
        start_random_layout = QHBoxLayout()
        start_random_layout.addWidget(self.chk_start_random)
        if settings_dialog:
            start_random_layout.addWidget(settings_dialog._create_modified_indicator('start_random'))
        path_layout.addLayout(start_random_layout)
        self.widgets['start_random'] = self.chk_start_random
        
        path_group.setLayout(path_layout)
        scroll_layout.addWidget(path_group)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
    
    def _connect_signals(self):
        """连接信号"""
        # 获取设置对话框实例
        settings_dialog = self._get_settings_dialog()
        
        if settings_dialog:
            # 文件操作设置
            settings_dialog._connect_modified_signal(self.chk_show_hidden, 'show_hidden_files', True)
            settings_dialog._connect_modified_signal(self.chk_show_all_sizes, 'show_all_sizes', False)
            
            # 搜索设置
            settings_dialog._connect_modified_signal(self.chk_search_hidden, 'search_hidden', False)
            
            # 路径设置
            settings_dialog._connect_modified_signal(self.chk_start_random, 'start_random', False)
    
    def _get_settings_dialog(self):
        """获取设置对话框实例
        
        由于GeneralTab是嵌套在QTabWidget中的，self.parent()返回的是QStackedWidget，
        需要通过多层parent()调用才能获取到真正的SettingsDialog实例
        """
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, '_on_setting_changed'):
                return parent
            parent = parent.parent()
        return None
    
    def save_settings(self):
        """保存设置"""
        settings = {
            'show_hidden_files': self.chk_show_hidden.isChecked(),
            'show_all_sizes': self.chk_show_all_sizes.isChecked(),
            'search_hidden': self.chk_search_hidden.isChecked(),
            'start_random': self.chk_start_random.isChecked()
        }
        return settings