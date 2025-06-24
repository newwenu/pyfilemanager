from PySide6.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QThread, Signal  # 线程相关导入
from datetime import datetime
import win32api
import win32con
import os
from utils.file_utils import format_size
from threads.folder_size import FolderSizeThread

# ：异步计算文件夹大小的线程类
class SizeCalculationThread(QThread):
    # 改为传递格式化后的字符串
    size_calculated = Signal(str)  # 关键修改
    
    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        # 计算原始大小后立即格式化
        raw_size = FolderSizeThread(self.folder_path).calculate_folder_size(self.folder_path)
        formatted_size = format_size(raw_size)  # 在子线程完成格式化
        self.size_calculated.emit(formatted_size)  # 发送格式化结果

class FilePropertiesDialog(QDialog):
    def __init__(self, parent, file_path):
        super().__init__(parent)
        self.parent = parent
        self.file_path = file_path
        self.setWindowTitle("文件属性")
        self._setup_ui()
        self._load_file_info()

    @staticmethod
    def show_for_selected_item(parent):
        # 保持原有逻辑不变
        selected = parent.file_list.selectedItems()
        if not selected:
            return
        item = selected[0]
        file_path = os.path.join(parent.current_path, item.text(0))
        dialog = FilePropertiesDialog(parent, file_path)
        dialog.exec()

    def _setup_ui(self):
        # 保持原有界面布局不变
        self.layout = QGridLayout(self)
        self.name_label = QLabel()
        self.path_label = QLabel()
        self.size_label = QLabel()  # 将显示计算状态或最终结果
        self.mtime_label = QLabel()
        self.btn_ok = QPushButton("确定")
        self.btn_ok.clicked.connect(self.accept)
        
        self.layout.addWidget(QLabel("名称:"), 0, 0)
        self.layout.addWidget(self.name_label, 0, 1)
        self.layout.addWidget(QLabel("路径:"), 1, 0)
        self.layout.addWidget(self.path_label, 1, 1)
        self.layout.addWidget(QLabel("大小:"), 2, 0)
        self.layout.addWidget(self.size_label, 2, 1)
        self.layout.addWidget(QLabel("修改时间:"), 3, 0)
        self.layout.addWidget(self.mtime_label, 3, 1)
        self.layout.addWidget(self.btn_ok, 4, 1, Qt.AlignmentFlag.AlignRight)

    def _load_file_info(self):
        """优化：异步加载文件夹大小"""
        try:
            # 立即获取可快速读取的属性
            mtime = datetime.fromtimestamp(os.path.getmtime(self.file_path))
            self.name_label.setText(os.path.basename(self.file_path))
            self.path_label.setText(self.file_path)
            self.mtime_label.setText(mtime.strftime('%Y-%m-%d %H:%M:%S'))

            # 文件大小直接读取，文件夹异步计算
            if os.path.isfile(self.file_path):
                size = os.path.getsize(self.file_path)
                self.size_label.setText(format_size(size))
            else:
                # 显示计算中提示并启动异步线程
                self.size_label.setText("大小计算中...")
                self.calc_thread = SizeCalculationThread(self.file_path)
                self.calc_thread.size_calculated.connect(self._update_folder_size)
                self.calc_thread.start()  # 启动后台线程

        except Exception as e:
            self.parent.show_error("错误", f"获取属性失败: {str(e)}")
            self.close()

    def _update_folder_size(self, formatted_size):
        # 直接使用格式化后的字符串
        self.size_label.setText(formatted_size)  # 无需再次调用format_size
        self.calc_thread.deleteLater()