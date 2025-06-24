from PySide6.QtWidgets import QLineEdit, QHBoxLayout, QWidget, QPushButton, QDialog, QFormLayout, QComboBox, QLabel, QDateTimeEdit, QSpinBox # 新增导入
from PySide6.QtCore import Qt,QDateTime
from PySide6.QtGui import QAction
import sys
import os
from time import sleep

import subprocess
from ctypes import windll
from PySide6.QtCore import QProcess, QTimer
from PySide6.QtWidgets import QVBoxLayout, QWidget
from PySide6.QtGui import QWindow

class SearchHandler:
    def __init__(self, main_window, file_list_updater):
        self.main_window = main_window
        self.file_list_updater = file_list_updater
        self.search_input = None
        self.enter_pressed = False  # 标记是否通过回车触发搜索
        self.is_visible = False  # 新增：记录当前是否可见
        self._init_ui()

    def _show_search_input(self):
        """切换显示/隐藏搜索输入框和工具栏"""
        if self.is_visible:
            # 再次按下时隐藏并清除过滤
            self._hide_toolbar()
            self.search_input.setVisible(False)
            self.file_list_updater.clear_filter()  # 新增：清除文件过滤
            self.is_visible = False
            self.enter_pressed = False  # 重置标记
            self.main_window.update_filelist()  # 新增：更新文件列表
        else:
            # 首次按下时显示
            self.main_window.toolbar.setVisible(True)
            self.search_input.setVisible(True)
            self.search_input.setFocus()
            self.is_visible = True
            self.main_window.statusBar().showMessage("简单搜索模式:")

    def _hide_toolbar(self):
        """隐藏工具栏（搜索完成或失去焦点时触发）"""
        self.main_window.toolbar.setVisible(False)  # 隐藏工具栏
        self.main_window.statusBar().showMessage("就绪",1000)  # 恢复默认状态

    def _init_ui(self):
        """初始化搜索输入框和高级搜索按钮（修改后）"""
        search_container = QWidget()
        layout = QHBoxLayout(search_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索文件...")
        self.search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_input)
        
        # 新增：高级搜索按钮
        self.advanced_btn = QPushButton("高级搜索")
        self.advanced_btn.clicked.connect(self._open_advanced_search)  # 绑定点击事件
        layout.addWidget(self.advanced_btn)  # 添加到工具栏
        
        self.main_window.toolbar.addWidget(search_container)
        self.main_window.toolbar.setVisible(False)  # 初始化隐藏

    def _on_search(self):
        """执行搜索逻辑（调用文件列表更新器过滤）"""
        self.enter_pressed = True  # 标记为通过回车触发
        keyword = self.search_input.text().strip()
        match_count = self.file_list_updater.filter_files(keyword)  # 获取匹配数量
        
        # 新增：无结果时显示提示
        if match_count == 0:
            self.main_window.statusBar().showMessage("未找到匹配文件", 3000)  # 状态栏显示3秒

    def _open_advanced_search(self):
        """打开高级搜索界面"""
        dialog = AdvancedSearchDialog(self.main_window)
        dialog.exec()

# 新增：高级搜索对话框类
class AdvancedSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Everything 搜索")
        # 移除固定尺寸设置（改为动态调整）
        # self.setFixedSize(800, 600)  # 原固定尺寸，需删除
        self.everything_process = None
        self.everything_window = None
        self.everything_exe_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../toolbox/Everythingsearch/Everything.exe"
        )
        self._init_ui()
        self._start_everything()

    def _embed_everything_window(self):
        """获取 Everything 窗口句柄并嵌入到对话框（修改后）"""
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