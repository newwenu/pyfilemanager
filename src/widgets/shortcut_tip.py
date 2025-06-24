from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt, QPoint

class ShortcutTipWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置窗口标志：无边框、置顶、工具窗口（不显示在任务栏）
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 背景透明
        
        # 提示文本标签
        self.label = QLabel(self)
        self.label.setStyleSheet("""
            QLabel {
                background: rgba(0, 0, 0, 180);  /* 半透明背景 */
                color: white;
                font-size: 12px;
                padding: 4px 8px;
                border-radius: 4px;
            }
        """)
    
    def set_text(self, text: str):
        """设置提示文本并调整大小"""
        self.label.setText(text)
        self.label.adjustSize()  # 根据文本内容自动调整标签大小
        self.adjustSize()  # 调整整个控件大小
    
    def show_beside(self, widget: QWidget):
        """将提示显示在目标部件的右侧中间位置（水平偏移10像素，垂直居中）"""
        # 获取目标部件的全局坐标（左上角）和尺寸
        global_pos = widget.mapToGlobal(QPoint(0, 0))  # 部件左上角全局坐标
        widget_width = widget.width()                  # 部件宽度
        widget_height = widget.height()                # 部件高度
        
        # 计算提示的显示位置：右侧中间（水平偏移10像素，垂直居中）
        tip_x = global_pos.x() + 10  # 右侧偏移10像素
        tip_y = global_pos.y() + 10
        self.move(tip_x, tip_y)
        self.show()
