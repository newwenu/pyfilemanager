from PySide6.QtWidgets import QLineEdit, QHBoxLayout, QWidget, QPushButton, QDialog 
import os
from time import sleep
from PySide6.QtCore import QProcess, QTimer
from PySide6.QtWidgets import QVBoxLayout, QWidget, QListWidget
from PySide6.QtGui import QWindow
import sys

# 导入事件总线
from core import event_bus


def is_admin() -> bool:
    """检测当前进程是否以管理员权限运行（Windows专用）"""
    if sys.platform != "win32":
        return False
    try:
        from ctypes import windll
        return windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


class SearchHandler:
    """搜索处理器 - 使用事件总线解耦"""
    
    def __init__(self, main_window, file_list_updater):
        self.main_window = main_window
        self.file_list_updater = file_list_updater
        self.search_input = None
        self.enter_pressed = False
        self.is_visible = False
        self.translation = main_window.translation
        self._init_ui()
        # 连接事件总线
        self._setup_event_bus_connections()
    
    def _setup_event_bus_connections(self):
        """设置事件总线连接"""
        # 注意：新版本的 SearchBox 组件已直接处理这些事件
        # 这里保留方法但不绑定，避免与新的 SearchBox 冲突
        # 如果需要使用旧的工具栏搜索功能，可以取消下面的注释
        # event_bus.focus_search_box.connect(self._on_focus_search)
        # event_bus.search_start.connect(self.start_search)
        # event_bus.search_clear.connect(self.clear_search)
        pass
    
    def _on_focus_search(self):
        """处理聚焦搜索框事件（事件总线回调）"""
        self._show_search_input()

    def _show_search_input(self):
        """切换显示/隐藏搜索输入框和工具栏（使用事件总线）"""
        if self.is_visible:
            # 再次按下时隐藏并清除过滤
            self._hide_toolbar()
            self.search_input.setVisible(False)
            self.file_list_updater.clear_filter()
            self.is_visible = False
            self.enter_pressed = False
            # 使用事件总线刷新文件列表
            event_bus.navigate_refresh.emit()
        else:
            # 首次按下时显示
            self.main_window.toolbar.setVisible(True)
            self.search_input.setVisible(True)
            self.search_input.setFocus()
            self.is_visible = True
            # 使用事件总线显示状态消息
            event_bus.ui_update_statusbar.emit(
                self.translation.get("search_status", "简单搜索模式:"), 0
            )

    def _hide_toolbar(self):
        """隐藏工具栏（使用事件总线）"""
        self.main_window.toolbar.setVisible(False)
        # 使用事件总线显示就绪状态
        event_bus.ui_update_statusbar.emit(
            self.translation.get("status_ready", "就绪"), 0
        )

    def _init_ui(self):
        """初始化搜索输入框和高级搜索按钮"""
        search_container = QWidget()
        layout = QHBoxLayout(search_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            self.translation.get("search_placeholder", "搜索文件...")
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_input)
        
        # 高级搜索按钮
        self.advanced_btn = QPushButton(
            self.translation.get("advanced_btn", "高级搜索")
        )
        self.advanced_btn.clicked.connect(self._open_advanced_search)
        layout.addWidget(self.advanced_btn)
        
        self.main_window.toolbar.addWidget(search_container)
        self.main_window.toolbar.setVisible(False)

    def _on_search(self):
        """执行搜索逻辑（使用事件总线）"""
        self.enter_pressed = True
        keyword = self.search_input.text().strip()
        match_count = self.file_list_updater.filter_files(keyword)
        
        # 无结果时显示提示（使用事件总线）
        if match_count == 0:
            event_bus.ui_update_statusbar.emit(
                self.translation.get("search_no_results", "未找到匹配文件"), 3000
            )

    def _open_advanced_search(self):
        """打开高级搜索界面（跨平台适配）"""
        if sys.platform == "win32":
            dialog = AdvancedSearchDialog(self.main_window)
            dialog.exec()
        else:
            dialog = LinuxAdvancedSearchDialog(self.main_window)
            dialog.exec()

    def start_search(self, keyword: str):
        """开始搜索（事件总线接口）"""
        if not self.is_visible:
            self._show_search_input()
        self.search_input.setText(keyword)
        self._on_search()

    def clear_search(self):
        """清除搜索（事件总线接口）"""
        if self.is_visible:
            self.search_input.clear()
            self.file_list_updater.clear_filter()


class LinuxAdvancedSearchDialog(QDialog):
    """Linux 高级搜索对话框"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(parent.translation.get("advanced_search", "高级搜索"))
        self.main_window = parent
        self.translation = parent.translation
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 搜索路径输入
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(
            self.translation.get("search_path", "搜索路径（留空为当前目录）")
        )
        layout.addWidget(self.path_input)
        
        # 关键字输入
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText(
            self.translation.get("search_keyword", "搜索关键字")
        )
        layout.addWidget(self.keyword_input)
        
        # 搜索按钮
        self.search_btn = QPushButton(
            self.translation.get("start_search", "开始搜索")
        )
        self.search_btn.clicked.connect(self._on_search)
        layout.addWidget(self.search_btn)
        
        # 结果显示
        self.result_list = QListWidget()
        layout.addWidget(self.result_list)

    def _on_search(self):
        """Linux 搜索逻辑"""
        path = self.path_input.text().strip() or self.main_window.current_path
        keyword = self.keyword_input.text().strip()
        
        results = []
        for root, dirs, files in os.walk(path):
            for file in files + dirs:
                if keyword in file:
                    results.append(os.path.join(root, file))
        
        self.result_list.clear()
        self.result_list.addItems(results)


class AdvancedSearchDialog(QDialog):
    """Windows Everything 高级搜索对话框"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.main_window = parent
        self.translation = parent.translation
        
        if sys.platform != "win32":
            return
        
        self.setWindowTitle(parent.translation.get("everything_search", "Everything 搜索"))
        self.everything_process = None
        self.everything_window = None
        self.everything_exe_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../toolbox/Everythingsearch/Everything.exe"
        )
        self._init_ui()
        self._start_everything()

    def _embed_everything_window(self):
        """仅 Windows 执行窗口嵌入"""
        if sys.platform != "win32":
            return
        from ctypes import windll
        hwnd = windll.user32.FindWindowW(None, "Everything")
        if not hwnd:
            sleep(2)
            hwnd = windll.user32.FindWindowW(None, "Everything")

        if not hwnd:
            print(self, "错误", "未找到 Everything 窗口，请确认已安装！")
            return
        
        original_style = windll.user32.GetWindowLongPtrW(hwnd, -16)
        windll.user32.SetParent(hwnd, int(self.winId()))
        windll.user32.SetWindowLongPtrW(hwnd, -16, original_style)

        window = QWindow.fromWinId(hwnd)
        if not window:
            print(self, "错误", "无法嵌入 Everything 窗口！")
            return

        everything_size = window.size()
        self.resize(everything_size.width() + 20, everything_size.height() + 40)

        container = QWidget.createWindowContainer(window, self)
        self.layout.addWidget(container)
        self.everything_window = window

    def _init_ui(self):
        self.layout = QVBoxLayout(self)

    def _start_everything(self):
        """启动 Everything 并嵌入其窗口"""
        if not os.path.exists(self.everything_exe_path):
            print(self.everything_exe_path)
            print(self, "错误", self.translation.get(
                "everything_not_found", 
                "项目内未找到 Everything.exe，请检查 toolbox/Everythingsearch 目录！"
            ))
            return

        if not is_admin():
            # 使用事件总线显示权限提示
            event_bus.ui_update_statusbar.emit(
                self.translation.get("everything_need_admin", "需要管理员权限以使用高级搜索功能"),
                3000
            )
            from PySide6.QtWidgets import QLabel
            label = QLabel(
                self.translation.get("everything_need_admin", "需要管理员权限以使用高级搜索功能")
            )
            self.layout.addWidget(label)
            self.close()
            return

        self.everything_process = QProcess(self)
        self.everything_process.start(self.everything_exe_path)
        QTimer.singleShot(100, self._embed_everything_window)

    def closeEvent(self, event):
        """关闭对话框时终止 Everything 进程"""
        if self.everything_process and self.everything_process.state() == QProcess.Running:
            self.everything_process.terminate()
            if not self.everything_process.waitForFinished(2000):
                self.everything_process.kill()
        super().closeEvent(event)
