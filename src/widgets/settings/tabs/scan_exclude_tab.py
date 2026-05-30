from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCheckBox,
                               QGroupBox, QScrollArea, QPushButton, QListWidget,
                               QListWidgetItem, QLineEdit, QLabel, QFileDialog,
                               QMessageBox)
from PySide6.QtCore import Qt
from src.widgets.settings.setting_item_group import SettingItemGroup


class ScanExcludeTab(QWidget):
    """扫描排除设置标签页"""
    
    def __init__(self, parent=None, config=None, widgets=None, translation=None):
        super().__init__(parent)
        self.config = config or {}
        self.widgets = widgets or {}
        self.translation = translation or {}
        self._items = SettingItemGroup(self)

        # 从配置加载数据
        self.hide_system_protected = self.config.get("scan_exclude_system_protected", False)
        self.custom_excludes = self.config.get("scan_exclude_custom", [])

        self._setup_ui()
        self._connect_signals()
    
    def _get_settings_dialog(self):
        """获取设置对话框实例"""
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, '_on_setting_changed'):
                return parent
            parent = parent.parent()
        return None
    
    def _setup_ui(self):
        """设置扫描排除标签页UI"""
        # 创建带滚动区域的布局
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        settings_dialog = self._get_settings_dialog()
        
        # ===== 系统保护文件区域 =====
        system_group = QGroupBox(self.translation.get("group_system_protected", "系统保护文件"))
        system_layout = QVBoxLayout(system_group)

        # 系统保护文件复选框
        self.chk_system_protected = self._items.add_checkbox(
            system_layout, 'scan_exclude_system_protected',
            self.translation.get("chk_system_protected", "排除受系统保护的文件（按属性识别）"),
            default_value=False
        )
        
        # 说明标签
        desc_label = QLabel(
            self.translation.get("desc_system_protected", 
                "Windows: 排除具有系统属性(S)的文件和目录，如 pagefile.sys、hiberfil.sys 等\n"
                "Linux/macOS: 排除系统关键文件")
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: gray; font-size: 12px;")
        system_layout.addWidget(desc_label)
        
        system_group.setLayout(system_layout)
        scroll_layout.addWidget(system_group)
        
        # ===== 自定义排除区域 =====
        custom_group = QGroupBox(self.translation.get("group_custom_excludes", "自定义排除目录/文件"))
        custom_layout = QVBoxLayout(custom_group)
        
        # 添加自定义排除项的输入区域
        add_layout = QHBoxLayout()
        self.custom_path_edit = QLineEdit()
        self.custom_path_edit.setPlaceholderText(self.translation.get("placeholder_custom_path", "输入路径或点击浏览选择..."))
        self.btn_browse_custom = QPushButton(self.translation.get("btn_browse", "浏览"))
        self.btn_add_custom = QPushButton(self.translation.get("btn_add", "添加"))
        add_layout.addWidget(self.custom_path_edit)
        add_layout.addWidget(self.btn_browse_custom)
        add_layout.addWidget(self.btn_add_custom)
        custom_layout.addLayout(add_layout)
        
        # 自定义排除列表
        self.custom_list_widget = QListWidget()
        self._load_custom_excludes()
        custom_layout.addWidget(self.custom_list_widget)
        
        # 删除按钮
        delete_layout = QHBoxLayout()
        delete_layout.addStretch()
        self.btn_delete_custom = QPushButton(self.translation.get("btn_delete", "删除选中项"))
        self.btn_clear_custom = QPushButton(self.translation.get("btn_clear_all", "清空全部"))
        delete_layout.addWidget(self.btn_delete_custom)
        delete_layout.addWidget(self.btn_clear_custom)
        custom_layout.addLayout(delete_layout)
        
        custom_group.setLayout(custom_layout)
        scroll_layout.addWidget(custom_group)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        

    
    def _load_custom_excludes(self):
        """加载自定义排除列表"""
        self.custom_list_widget.clear()
        for path in self.custom_excludes:
            self._add_custom_item(path)
    
    def _add_custom_item(self, path):
        """添加自定义排除项到列表"""
        item = QListWidgetItem(path)
        item.setData(Qt.UserRole, path)
        item.setToolTip(path)
        self.custom_list_widget.addItem(item)
    
    def _connect_signals(self):
        """连接信号"""
        # 系统保护文件复选框
        self.chk_system_protected.stateChanged.connect(self._on_system_protected_changed)
        
        # 自定义排除操作
        self.btn_browse_custom.clicked.connect(self._browse_custom_path)
        self.btn_add_custom.clicked.connect(self._add_custom_exclude)
        self.custom_path_edit.returnPressed.connect(self._add_custom_exclude)
        self.btn_delete_custom.clicked.connect(self._delete_custom_exclude)
        self.btn_clear_custom.clicked.connect(self._clear_custom_excludes)
    
    def _on_system_protected_changed(self):
        """系统保护文件选项改变"""
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            settings_dialog._on_setting_changed('scan_exclude_system_protected', self.chk_system_protected.isChecked())
    
    def _browse_custom_path(self):
        """浏览选择自定义排除路径"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.translation.get("select_type", "选择类型"))
        msg_box.setText(self.translation.get("select_file_or_folder", "请选择要排除的是文件还是文件夹？"))
        btn_file = msg_box.addButton(self.translation.get("file", "文件"), QMessageBox.YesRole)
        btn_folder = msg_box.addButton(self.translation.get("folder", "文件夹"), QMessageBox.NoRole)
        btn_cancel = msg_box.addButton(QMessageBox.Cancel)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == btn_file:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                self.translation.get("select_file_to_exclude", "选择要排除的文件"),
                "",
                self.translation.get("all_files", "所有文件 (*.*)")
            )
            if file_path:
                self.custom_path_edit.setText(file_path)
        elif msg_box.clickedButton() == btn_folder:
            folder_path = QFileDialog.getExistingDirectory(
                self,
                self.translation.get("select_folder_to_exclude", "选择要排除的文件夹"),
                ""
            )
            if folder_path:
                self.custom_path_edit.setText(folder_path)
    
    def _add_custom_exclude(self):
        """添加自定义排除项"""
        path = self.custom_path_edit.text().strip()
        if not path:
            QMessageBox.warning(
                self,
                self.translation.get("warning", "警告"),
                self.translation.get("please_enter_path", "请输入路径")
            )
            return
        
        # 检查是否已存在
        if path in self.get_custom_excludes():
            QMessageBox.information(
                self,
                self.translation.get("info", "提示"),
                self.translation.get("path_already_exists", "该路径已存在于排除列表中")
            )
            return
        
        self._add_custom_item(path)
        self.custom_path_edit.clear()
        
        # 通知设置改变
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            settings_dialog._on_setting_changed('scan_exclude_custom', self.get_custom_excludes())
    
    def _delete_custom_exclude(self):
        """删除选中的自定义排除项"""
        current_row = self.custom_list_widget.currentRow()
        if current_row >= 0:
            self.custom_list_widget.takeItem(current_row)
            
            # 通知设置改变
            settings_dialog = self._get_settings_dialog()
            if settings_dialog:
                settings_dialog._on_setting_changed('scan_exclude_custom', self.get_custom_excludes())
        else:
            QMessageBox.information(
                self,
                self.translation.get("info", "提示"),
                self.translation.get("please_select_item_to_delete", "请选择要删除的项")
            )
    
    def _clear_custom_excludes(self):
        """清空所有自定义排除项"""
        if self.custom_list_widget.count() == 0:
            return
            
        reply = QMessageBox.question(
            self,
            self.translation.get("confirm", "确认"),
            self.translation.get("confirm_clear_all", "确定要清空所有自定义排除项吗？"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.custom_list_widget.clear()
            
            # 通知设置改变
            settings_dialog = self._get_settings_dialog()
            if settings_dialog:
                settings_dialog._on_setting_changed('scan_exclude_custom', [])
    
    def get_custom_excludes(self):
        """获取自定义排除项列表"""
        excludes = []
        for i in range(self.custom_list_widget.count()):
            item = self.custom_list_widget.item(i)
            path = item.data(Qt.UserRole)
            excludes.append(path)
        return excludes
    
    def get_exclude_settings(self):
        """获取所有排除设置数据"""
        return {
            'scan_exclude_system_protected': self.chk_system_protected.isChecked(),
            'scan_exclude_custom': self.get_custom_excludes()
        }
