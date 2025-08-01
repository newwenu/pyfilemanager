from PySide6.QtWidgets import QLineEdit, QHBoxLayout, QWidget, QPushButton, QDialog 
import os
from time import sleep
from ctypes import windll
from PySide6.QtCore import QProcess, QTimer
from PySide6.QtWidgets import QVBoxLayout, QWidget,QListWidget
from PySide6.QtGui import QWindow
import sys  # 新增：用于系统判断

class SearchHandler:
    def __init__(self, main_window, file_list_updater):

        self.main_window = main_window
        self.file_list_updater = file_list_updater
        self.search_input = None
        self.enter_pressed = False  # 标记是否通过回车触发搜索
        self.is_visible = False  # ：记录当前是否可见
        self.translation = main_window.translation  # 获取主窗口的翻译对象
        self._init_ui()

    def _show_search_input(self):
        """切换显示/隐藏搜索输入框和工具栏"""
        if self.is_visible:
            # 再次按下时隐藏并清除过滤
            self._hide_toolbar()
            self.search_input.setVisible(False)
            self.file_list_updater.clear_filter()  # ：清除文件过滤
            self.is_visible = False
            self.enter_pressed = False  # 重置标记
            self.main_window.update_filelist()  # ：更新文件列表
        else:
            # 首次按下时显示
            self.main_window.toolbar.setVisible(True)
            self.search_input.setVisible(True)
            self.search_input.setFocus()
            self.is_visible = True
            self.main_window.statusBar().showMessage(self.translation.get("search_status", "简单搜索模式:"))

    def _hide_toolbar(self):
        """隐藏工具栏（搜索完成或失去焦点时触发）"""
        self.main_window.toolbar.setVisible(False)  # 隐藏工具栏
        self.main_window.statusBar().showMessage(self.translation.get("status_ready", "就绪"))
        
        # self.main_window.statusBar().showMessage("就绪",1000)  # 恢复默认状态

    def _init_ui(self):
        """初始化搜索输入框和高级搜索按钮（修改后）"""
        search_container = QWidget()
        layout = QHBoxLayout(search_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 搜索输入框
        self.search_input = QLineEdit()
        # self.search_input.setPlaceholderText("搜索文件...")
        self.search_input.setPlaceholderText(self.translation.get("search_placeholder", "搜索文件..."))
        self.search_input.setClearButtonEnabled(True)  # 启用清除按钮
        self.search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_input)
        
        # ：高级搜索按钮
        # self.advanced_btn = QPushButton("高级搜索")
        self.advanced_btn = QPushButton(self.translation.get("advanced_btn", "高级搜索"))

        self.advanced_btn.clicked.connect(self._open_advanced_search)  # 绑定点击事件
        layout.addWidget(self.advanced_btn)  # 添加到工具栏
        
        self.main_window.toolbar.addWidget(search_container)
        self.main_window.toolbar.setVisible(False)  # 初始化隐藏

    def _on_search(self):
        """执行搜索逻辑（调用文件列表更新器过滤）"""
        self.enter_pressed = True  # 标记为通过回车触发
        keyword = self.search_input.text().strip()
        match_count = self.file_list_updater.filter_files(keyword)  # 获取匹配数量
        
        # ：无结果时显示提示
        if match_count == 0:
            # self.main_window.statusBar().showMessage("未找到匹配文件", 3000)  # 状态栏显示3秒
            self.main_window.statusBar().showMessage(self.translation.get("search_no_results", "未找到匹配文件"), 3000)

    def _open_advanced_search(self):
        """打开高级搜索界面（跨平台适配）"""
        if sys.platform == "win32":
            # Windows 继续使用 Everything
            dialog = AdvancedSearchDialog(self.main_window)
            dialog.exec()
        else:
            # Linux 使用 Qt 内置搜索或调用 locate 命令
            dialog = LinuxAdvancedSearchDialog(self.main_window)
            dialog.exec()

# 新增：Linux 高级搜索对话框类
class LinuxAdvancedSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(parent.translation.get("advanced_search", "高级搜索"))
        self.main_window = parent
        self.translation = parent.translation
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 搜索路径输入
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(self.translation.get("search_path", "搜索路径（留空为当前目录）"))
        layout.addWidget(self.path_input)
        
        # 关键字输入
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText(self.translation.get("search_keyword", "搜索关键字"))
        layout.addWidget(self.keyword_input)
        
        # 搜索按钮
        self.search_btn = QPushButton(self.translation.get("start_search", "开始搜索"))
        self.search_btn.clicked.connect(self._on_search)
        layout.addWidget(self.search_btn)
        
        # 结果显示
        self.result_list = QListWidget()
        layout.addWidget(self.result_list)

    def _on_search(self):
        """Linux 搜索逻辑（调用 locate 命令或 os.walk）"""
        path = self.path_input.text().strip() or self.main_window.current_path
        keyword = self.keyword_input.text().strip()
        
        # 示例：使用 os.walk 遍历目录（可替换为调用 locate 命令通过 QProcess 执行）
        results = []
        for root, dirs, files in os.walk(path):
            for file in files + dirs:
                if keyword in file:
                    results.append(os.path.join(root, file))
        
        self.result_list.clear()
        self.result_list.addItems(results)

# ：高级搜索对话框类
class AdvancedSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        if sys.platform != "win32":
            return  # Linux 不初始化此对话框（已由 LinuxAdvancedSearchDialog 替代）
        
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
        
        hwnd = windll.user32.FindWindowW(None, "Everything")
        if not hwnd:
            sleep(2)
            hwnd = windll.user32.FindWindowW(None, "Everything")

        if not hwnd:
            print(self, "错误", "未找到 Everything 窗口，请确认已安装！")
            return
         # 获取原窗口样式（避免覆盖工具栏相关样式）
        original_style = windll.user32.GetWindowLongPtrW(hwnd, -16)  # GWL_STYLE = -16
        # 设置父窗口为当前对话框的窗口句柄（确保嵌入到 Qt 界面中）
        windll.user32.SetParent(hwnd, int(self.winId()))
        # 恢复原窗口样式（保留工具栏等原生元素）
        windll.user32.SetWindowLongPtrW(hwnd, -16, original_style)

        window = QWindow.fromWinId(hwnd)
        if not window:
            print(self, "错误", "无法嵌入 Everything 窗口！")
            return

        # 获取 Everything 窗口的实际尺寸
        everything_size = window.size()
        # 调整对话框大小为 Everything 窗口尺寸（+ 可能的边框补偿，根据实际情况调整）
        self.resize(everything_size.width()+20, everything_size.height()+40)

        container = QWidget.createWindowContainer(window, self)
        self.layout.addWidget(container)
        self.everything_window = window

    def _init_ui(self):
        self.layout = QVBoxLayout(self)

    def _start_everything(self):
        """启动 Everything 并嵌入其窗口（修改后）"""
        # 校验路径是否存在
        if not os.path.exists(self.everything_exe_path):
            print(self.everything_exe_path)
            print(self, "错误", "项目内未找到 Everything.exe，请检查 toolbox/Everythingsearch 目录！")
            return
        i=0
        self.everything_process = QProcess(self)
        self.everything_process.start(self.everything_exe_path)  # 使用项目内的绝对路径启动
        QTimer.singleShot(1000, self._embed_everything_window)

    def closeEvent(self, event):
        """关闭对话框时终止 Everything 进程（修复后）"""
        if self.everything_process and self.everything_process.state() == QProcess.Running:
            self.everything_process.terminate()  # 发送终止信号
            # 等待最多2秒，确保进程完全退出
            if not self.everything_process.waitForFinished(2000):
                self.everything_process.kill()  # 强制终止（如果等待超时）
        super().closeEvent(event)