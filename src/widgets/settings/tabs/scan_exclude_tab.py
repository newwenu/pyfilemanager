from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, 
                               QGroupBox, QScrollArea, QPushButton, QListWidget, 
                               QListWidgetItem, QLineEdit, QLabel, QFileDialog,
                               QMessageBox)
from PySide6.QtCore import Qt


class ScanExcludeTab(QWidget):
    """扫描排除设置标签页"""
    
    # 系统关键文件默认列表
    DEFAULT_SYSTEM_EXCLUDES = [
        {"name": "pagefile.sys", "desc": "Windows 页面文件", "checked": True},
        {"name": "hiberfil.sys", "desc": "Windows 休眠文件", "checked": True},
        {"name": "$RECYCLE.BIN", "desc": "回收站", "checked": True},
        {"name": "System Volume Information", "desc": "系统卷标信息", "checked": True},
        {"name": "swapfile.sys", "desc": "交换文件", "checked": True}
    ]
    
    def __init__(self, parent=None, config=None, widgets=None, translation=None):
        super().__init__(parent)
        self.config = config or {}
        self.widgets = widgets or {}
        self.translation = translation or {}
        
        # 从配置加载数据
        self.system_excludes = self.config.get("scan_exclude_system", self.DEFAULT_SYSTEM_EXCLUDES.copy())
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
        
        # ===== 系统关键文件区域 =====
        system_group = QGroupBox(self.translation.get("group_system_excludes", "系统关键文件（扫描时排除）"))
        system_layout = QVBoxLayout(system_group)
        
        # 全选/取消全选按钮
        select_all_layout = QHBoxLayout()
        self.btn_select_all_system = QPushButton(self.translation.get("btn_select_all", "全选"))
        self.btn_deselect_all_system = QPushButton(self.translation.get("btn_deselect_all", "取消全选"))
        select_all_layout.addWidget(self.btn_select_all_system)
        select_all_layout.addWidget(self.btn_deselect_all_system)
        select_all_layout.addStretch()
        system_layout.addLayout(select_all_layout)
        
        # 系统文件列表
        self.system_list_widget = QListWidget()
        self._load_system_excludes()
        system_layout.addWidget(self.system_list_widget)
        
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
        
        # 存储控件引用
        self.widgets['scan_exclude_system'] = self.system_list_widget
        self.widgets['scan_exclude_custom'] = self.custom_list_widget
    
    def _load_system_excludes(self):
        """加载系统关键文件列表"""
        self.system_list_widget.clear()
        for item_data in self.system_excludes:
            item = QListWidgetItem()
            checkbox = QCheckBox(f"{item_data['name']} - {item_data.get('desc', '')}")
            checkbox.setChecked(item_data.get('checked', True))
            checkbox.stateChanged.connect(self._on_system_exclude_changed)
            
            self.system_list_widget.addItem(item)
            self.system_list_widget.setItemWidget(item, checkbox)
            # 存储数据到item
            item.setData(Qt.UserRole, item_data['name'])
    
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
        # 系统文件全选/取消全选
        self.btn_select_all_system.clicked.connect(self._select_all_system)
        self.btn_deselect_all_system.clicked.connect(self._deselect_all_system)
        
        # 自定义排除操作
        self.btn_browse_custom.clicked.connect(self._browse_custom_path)
        self.btn_add_custom.clicked.connect(self._add_custom_exclude)
        self.custom_path_edit.returnPressed.connect(self._add_custom_exclude)
        self.btn_delete_custom.clicked.connect(self._delete_custom_exclude)
        self.btn_clear_custom.clicked.connect(self._clear_custom_excludes)
    
    def _on_system_exclude_changed(self):
        """系统排除项状态改变"""
        settings_dialog = self._get_settings_dialog()
        if settings_dialog:
            settings_dialog._on_setting_changed('scan_exclude_system', self.get_system_excludes_data())
    
    def _select_all_system(self):
        """全选系统关键文件"""
        for i in range(self.system_list_widget.count()):
            item = self.system_list_widget.item(i)
            checkbox = self.system_list_widget.itemWidget(item)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(True)
        self._on_system_exclude_changed()
    
    def _deselect_all_system(self):
        """取消全选系统关键文件"""
        for i in range(self.system_list_widget.count()):
            item = self.system_list_widget.item(i)
            checkbox = self.system_list_widget.itemWidget(item)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(False)
        self._on_system_exclude_changed()
    
    def _browse_custom_path(self):
        """浏览选择自定义排除路径"""
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        
        # 创建自定义对话框，允许选择文件或文件夹
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
    
    def get_system_excludes_data(self):
        """获取系统排除项数据"""
        data = []
        for i in range(self.system_list_widget.count()):
            item = self.system_list_widget.item(i)
            checkbox = self.system_list_widget.itemWidget(item)
            name = item.data(Qt.UserRole)
            if isinstance(checkbox, QCheckBox):
                # 从checkbox文本中提取描述
                text = checkbox.text()
                desc = text.split(" - ")[1] if " - " in text else ""
                data.append({
                    "name": name,
                    "desc": desc,
                    "checked": checkbox.isChecked()
                })
        return data
    
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
            'scan_exclude_system': self.get_system_excludes_data(),
            'scan_exclude_custom': self.get_custom_excludes()
        }
