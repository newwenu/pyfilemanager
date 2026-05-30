"""
更多选项按钮组件

提供右上角三个点按钮，点击展开菜单包含：
- 显示隐藏文件
- 显示所有大小
- 刷新
"""
from PySide6.QtWidgets import QPushButton, QMenu
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt, Signal


class MoreOptionsButton(QPushButton):
    """更多选项按钮 - 直接继承 QPushButton"""

    # 信号
    toggle_hidden_files = Signal(bool)  # 切换显示隐藏文件
    toggle_show_sizes = Signal(bool)    # 切换显示所有大小
    refresh_requested = Signal()        # 刷新请求

    def __init__(self, parent=None, translation=None, config=None, bg_color=None):
        super().__init__(parent)
        self.translation = translation or {}
        self._config = config or {}  # 本地配置副本，不修改全局配置
        self.bg_color = bg_color or "rgba(0, 0, 0, 60)"  # 默认背景色
        self._setup_ui()

    def _setup_ui(self):
        """初始化UI"""
        # 设置按钮文本和样式
        self.setText("⋮")  # 三个垂直点
        self.setFixedSize(26, 26)
        self.setFlat(True)
        # 使用传入的背景色
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.bg_color};
                border: none;
                border-radius: 3px;
                color: #eeeeee;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 40);
                color: #ffffff;
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 60);
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self._on_button_clicked)
        
        # 创建菜单
        self._setup_menu()

    def _setup_menu(self):
        """设置菜单"""
        self.menu = QMenu(self)
        self.menu.setStyleSheet("""
            QMenu {
                background-color: rgba(50, 50, 50, 240);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                color: #cccccc;
                padding: 6px 20px;
                font-size: 12px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 30);
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(255, 255, 255, 30);
                margin: 4px 8px;
            }
        """)

        # 显示隐藏文件选项
        self.action_show_hidden = QAction(
            self.translation.get("cb_hidden", "显示隐藏文件"),
            self,
            checkable=True
        )
        self.action_show_hidden.setChecked(self._config.get("show_hidden_files", False))
        self.action_show_hidden.triggered.connect(self._on_toggle_hidden_files)
        self.menu.addAction(self.action_show_hidden)

        # 显示所有大小选项
        self.action_show_sizes = QAction(
            self.translation.get("cb_show_sizes", "显示所有大小"),
            self,
            checkable=True
        )
        self.action_show_sizes.setChecked(self._config.get("show_all_sizes", False))
        self.action_show_sizes.triggered.connect(self._on_toggle_show_sizes)
        self.menu.addAction(self.action_show_sizes)

        # 分隔线
        self.menu.addSeparator()

        # 刷新选项
        self.action_refresh = QAction(
            self.translation.get("refresh", "刷新"),
            self
        )
        self.action_refresh.setShortcut(QKeySequence("F5"))
        self.action_refresh.triggered.connect(self._on_refresh)
        self.menu.addAction(self.action_refresh)

    def _on_button_clicked(self):
        """按钮点击 - 显示菜单"""
        self.menu.exec(self.mapToGlobal(
            self.rect().bottomLeft()
        ))

    def _on_toggle_hidden_files(self, checked: bool):
        """切换显示隐藏文件 - 只发射信号，不修改全局配置"""
        self.toggle_hidden_files.emit(checked)

    def _on_toggle_show_sizes(self, checked: bool):
        """切换显示所有大小 - 只发射信号，不修改全局配置"""
        self.toggle_show_sizes.emit(checked)

    def _on_refresh(self):
        """刷新"""
        self.refresh_requested.emit()

    def update_config(self, config: dict):
        """更新配置显示（从外部传入最新配置）"""
        self._config = config
        self.action_show_hidden.setChecked(config.get("show_hidden_files", False))
        self.action_show_sizes.setChecked(config.get("show_all_sizes", False))
