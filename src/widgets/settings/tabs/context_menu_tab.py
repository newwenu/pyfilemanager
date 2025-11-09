from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLabel, QCheckBox, QPushButton, QGroupBox, QScrollArea)
from PySide6.QtCore import Qt

class ContextMenuTab(QWidget):
    """右键菜单设置标签页"""
    
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
        """设置右键菜单标签页UI"""
        # 创建带滚动区域的布局
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 文件列表右键菜单组
        file_list_group = QGroupBox(self.translation.get("group_file_list_menu", "文件列表右键菜单"))
        file_list_layout = QVBoxLayout(file_list_group)
        
        # 显示删除选项
        self.show_delete_checkbox = QCheckBox(self.translation.get("chk_show_delete", "显示删除选项"))
        self.show_delete_checkbox.setChecked(self.config.get("show_context_menu_delete", True))
        show_delete_layout = QHBoxLayout()
        show_delete_layout.addWidget(self.show_delete_checkbox)
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            show_delete_layout.addWidget(settings_dialog._create_modified_indicator('show_context_menu_delete'))
        show_delete_layout.setContentsMargins(0, 0, 0, 0)
        file_list_layout.addLayout(show_delete_layout)
        self.widgets['show_context_menu_delete'] = self.show_delete_checkbox
        
        # 显示属性选项
        self.show_properties_checkbox = QCheckBox(self.translation.get("chk_show_properties", "显示属性选项"))
        self.show_properties_checkbox.setChecked(self.config.get("show_context_menu_properties", True))
        show_properties_layout = QHBoxLayout()
        show_properties_layout.addWidget(self.show_properties_checkbox)
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            show_properties_layout.addWidget(settings_dialog._create_modified_indicator('show_context_menu_properties'))
        show_properties_layout.setContentsMargins(0, 0, 0, 0)
        file_list_layout.addLayout(show_properties_layout)
        self.widgets['show_context_menu_properties'] = self.show_properties_checkbox
        
        # 显示在资源管理器打开选项
        self.show_open_explorer_checkbox = QCheckBox(self.translation.get("chk_show_open_explorer", "显示在资源管理器打开选项"))
        self.show_open_explorer_checkbox.setChecked(self.config.get("show_context_menu_open_explorer", True))
        show_open_explorer_layout = QHBoxLayout()
        show_open_explorer_layout.addWidget(self.show_open_explorer_checkbox)
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            show_open_explorer_layout.addWidget(settings_dialog._create_modified_indicator('show_context_menu_open_explorer'))
        show_open_explorer_layout.setContentsMargins(0, 0, 0, 0)
        file_list_layout.addLayout(show_open_explorer_layout)
        self.widgets['show_context_menu_open_explorer'] = self.show_open_explorer_checkbox
        
        # 显示新建文件夹选项
        self.show_new_folder_checkbox = QCheckBox(self.translation.get("chk_show_new_folder", "显示新建文件夹选项"))
        self.show_new_folder_checkbox.setChecked(self.config.get("show_context_menu_new_folder", True))
        show_new_folder_layout = QHBoxLayout()
        show_new_folder_layout.addWidget(self.show_new_folder_checkbox)
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            show_new_folder_layout.addWidget(settings_dialog._create_modified_indicator('show_context_menu_new_folder'))
        show_new_folder_layout.setContentsMargins(0, 0, 0, 0)
        file_list_layout.addLayout(show_new_folder_layout)
        self.widgets['show_context_menu_new_folder'] = self.show_new_folder_checkbox
        
        scroll_layout.addWidget(file_list_group)
        
        # 空白区域右键菜单组
        blank_area_group = QGroupBox(self.translation.get("group_blank_area_menu", "空白区域右键菜单"))
        blank_area_layout = QVBoxLayout(blank_area_group)
        
        # 显示新建文件夹选项（空白区域）
        self.show_blank_new_folder_checkbox = QCheckBox(self.translation.get("chk_show_blank_new_folder", "显示新建文件夹选项"))
        self.show_blank_new_folder_checkbox.setChecked(self.config.get("show_blank_menu_new_folder", True))
        show_blank_new_folder_layout = QHBoxLayout()
        show_blank_new_folder_layout.addWidget(self.show_blank_new_folder_checkbox)
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            show_blank_new_folder_layout.addWidget(settings_dialog._create_modified_indicator('show_blank_menu_new_folder'))
        show_blank_new_folder_layout.setContentsMargins(0, 0, 0, 0)
        blank_area_layout.addLayout(show_blank_new_folder_layout)
        self.widgets['show_blank_menu_new_folder'] = self.show_blank_new_folder_checkbox
        
        # 显示在资源管理器打开选项（空白区域）
        self.show_blank_open_explorer_checkbox = QCheckBox(self.translation.get("chk_show_blank_open_explorer", "显示在资源管理器打开选项"))
        self.show_blank_open_explorer_checkbox.setChecked(self.config.get("show_blank_menu_open_explorer", True))
        show_blank_open_explorer_layout = QHBoxLayout()
        show_blank_open_explorer_layout.addWidget(self.show_blank_open_explorer_checkbox)
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            show_blank_open_explorer_layout.addWidget(settings_dialog._create_modified_indicator('show_blank_menu_open_explorer'))
        show_blank_open_explorer_layout.setContentsMargins(0, 0, 0, 0)
        blank_area_layout.addLayout(show_blank_open_explorer_layout)
        self.widgets['show_blank_menu_open_explorer'] = self.show_blank_open_explorer_checkbox
        
        scroll_layout.addWidget(blank_area_group)
        
        # 添加重置按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.btn_reset_menu = QPushButton(self.translation.get("btn_reset_menu", "重置为默认"))
        button_layout.addWidget(self.btn_reset_menu)
        scroll_layout.addLayout(button_layout)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
    
    def _connect_signals(self):
        """连接信号"""
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            # 复选框信号
            self.show_delete_checkbox.stateChanged.connect(
                lambda state: settings_dialog._on_setting_changed('show_context_menu_delete', state == Qt.CheckState.Checked, True))
            
            self.show_properties_checkbox.stateChanged.connect(
                lambda state: settings_dialog._on_setting_changed('show_context_menu_properties', state == Qt.CheckState.Checked, True))
            
            self.show_open_explorer_checkbox.stateChanged.connect(
                lambda state: settings_dialog._on_setting_changed('show_context_menu_open_explorer', state == Qt.CheckState.Checked, True))
            
            self.show_new_folder_checkbox.stateChanged.connect(
                lambda state: settings_dialog._on_setting_changed('show_context_menu_new_folder', state == Qt.CheckState.Checked, True))
            
            self.show_blank_new_folder_checkbox.stateChanged.connect(
                lambda state: settings_dialog._on_setting_changed('show_blank_menu_new_folder', state == Qt.CheckState.Checked, True))
            
            self.show_blank_open_explorer_checkbox.stateChanged.connect(
                lambda state: settings_dialog._on_setting_changed('show_blank_menu_open_explorer', state == Qt.CheckState.Checked, True))
        
        # 重置按钮信号
        self.btn_reset_menu.clicked.connect(self._reset_to_default)
    
    def _reset_to_default(self):
        """重置为默认设置"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            self.translation.get("dlg_confirm", "确认"),
            self.translation.get("dlg_reset_menu_confirm", "确定要重置右键菜单设置为默认值吗？"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 重置所有复选框为默认值
            self.show_delete_checkbox.setChecked(True)
            self.show_properties_checkbox.setChecked(True)
            self.show_open_explorer_checkbox.setChecked(True)
            self.show_new_folder_checkbox.setChecked(True)
            self.show_blank_new_folder_checkbox.setChecked(True)
            self.show_blank_open_explorer_checkbox.setChecked(True)