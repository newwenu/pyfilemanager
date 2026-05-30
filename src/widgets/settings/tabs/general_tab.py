from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QScrollArea)
from src.widgets.settings.setting_item_group import SettingItemGroup


class GeneralTab(QWidget):
    """常规设置标签页"""

    def __init__(self, parent=None, config=None, widgets=None, translation=None):
        super().__init__(parent)
        self.config = config or {}
        self.widgets = widgets or {}
        self.translation = translation or {}
        self._items = SettingItemGroup(self)
        self._setup_ui()

    def _setup_ui(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 文件视图组
        file_group = QGroupBox(self.translation.get("group_file_operations", "文件视图"))
        file_layout = QVBoxLayout(file_group)

        self.chk_show_hidden = self._items.add_checkbox(
            file_layout, 'show_hidden_files',
            self.translation.get("chk_show_hidden", "显示隐藏文件和文件夹"),
            default_value=True
        )

        self.chk_show_all_sizes = self._items.add_checkbox(
            file_layout, 'show_all_sizes',
            self.translation.get("chk_show_folder_sizes", "显示所有文件夹大小"),
            default_value=False
        )

        self.chk_show_mtime = self._items.add_checkbox(
            file_layout, 'show_mtime',
            self.translation.get("chk_show_mtime", "显示修改时间"),
            default_value=False
        )

        file_group.setLayout(file_layout)
        scroll_layout.addWidget(file_group)

        # 搜索组
        search_group = QGroupBox(self.translation.get("group_search", "搜索"))
        search_layout = QVBoxLayout(search_group)

        self.chk_search_hidden = self._items.add_checkbox(
            search_layout, 'search_hidden',
            self.translation.get("chk_search_hidden", "搜索时包含隐藏文件"),
            default_value=False
        )

        search_group.setLayout(search_layout)
        scroll_layout.addWidget(search_group)

        # 路径组
        path_group = QGroupBox(self.translation.get("group_path", "路径"))
        path_layout = QVBoxLayout(path_group)

        self.chk_start_random = self._items.add_checkbox(
            path_layout, 'start_random',
            self.translation.get("chk_start_random_bg", "启动时随机显示图片"),
            default_value=False
        )

        path_group.setLayout(path_layout)
        scroll_layout.addWidget(path_group)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def save_settings(self):
        return {
            'show_hidden_files': self.chk_show_hidden.isChecked(),
            'show_all_sizes': self.chk_show_all_sizes.isChecked(),
            'show_mtime': self.chk_show_mtime.isChecked(),
            'search_hidden': self.chk_search_hidden.isChecked(),
            'start_random': self.chk_start_random.isChecked()
        }