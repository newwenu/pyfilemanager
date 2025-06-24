from PySide6.QtWidgets import QTreeWidget
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt

class FileListWidget(QTreeWidget):
    """自定义 QTreeWidget，支持在空状态时显示提示文本"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._empty_hint = ""  # 初始无提示

    def set_empty_hint(self, text: str):
        """设置空状态提示文本"""
        self._empty_hint = text
        # super().update()  # 触发重绘
        self.viewport().update()  # 关键修改：通过视口触发无参重绘


    def paintEvent(self, event):
        """重写绘制事件：空状态时绘制提示文本"""
        if self.topLevelItemCount() == 0 and self._empty_hint:
            # 无内容且有提示时，在中心绘制灰色文本
            painter = QPainter(self.viewport())
            painter.setPen(QColor(Qt.gray))
            painter.drawText(self.rect(), Qt.AlignCenter, self._empty_hint)
        else:
            # 正常绘制原有内容
            super().paintEvent(event)
