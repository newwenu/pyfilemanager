"""
搜索框组件

支持快捷键唤起的搜索输入框
平时隐藏，需要时出现
"""
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, 
                               QPushButton, QLabel, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont


class SearchBox(QWidget):
    """搜索框组件"""
    
    # 信号：搜索文本变化、搜索确认、关闭搜索
    search_text_changed = Signal(str)
    search_confirmed = Signal(str)
    search_closed = Signal()
    
    def __init__(self, parent=None, translation=None, bg_color=None):
        super().__init__(parent)
        self.translation = translation or {}
        self.bg_color = bg_color or "rgba(50, 50, 50, 240)"
        self._setup_ui()
        self._setup_animations()
        
    def _setup_ui(self):
        """初始化UI"""
        # 不固定高度，由外部调用者设置
        self.setVisible(False)  # 默认隐藏
        
        # 启用样式背景绘制
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)  # 减小边距
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # 垂直居中
        
        # 搜索图标
        self.search_icon = QLabel("🔍")
        self.search_icon.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.search_icon)
        
        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            self.translation.get("search_placeholder", "搜索当前文件夹...")
        )
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.returnPressed.connect(self._on_search_confirmed)
        layout.addWidget(self.search_input, 1)
        
        # 清除按钮
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFixedSize(20, 20)
        self.clear_btn.setFlat(True)
        self.clear_btn.setVisible(False)
        self.clear_btn.clicked.connect(self._on_clear)
        layout.addWidget(self.clear_btn)
        
        # 关闭按钮
        self.close_btn = QPushButton("Esc")
        self.close_btn.setFixedSize(40, 22)
        self.close_btn.setFlat(True)
        self.close_btn.clicked.connect(self.hide_search)
        layout.addWidget(self.close_btn)
        
        # 应用样式
        self._apply_style()
        
    def _apply_style(self):
        """应用样式 - 使用传入的背景色"""
        self.setStyleSheet(f"""
            SearchBox {{
                background-color: {self.bg_color};
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 50);
            }}
            QLineEdit {{
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-size: 12px;
                padding: 2px;
            }}
            QPushButton {{
                background-color: rgba(255, 255, 255, 30);
                border: none;
                border-radius: 2px;
                color: #cccccc;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 50);
                color: #ffffff;
            }}
        """)
        
    def _setup_animations(self):
        """设置动画"""
        # 透明度动画
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
    def show_search(self):
        """显示搜索框"""
        self.setVisible(True)
        self.search_input.setFocus()
        self.search_input.selectAll()
        
        # 淡入动画
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.start()
        
    def hide_search(self):
        """隐藏搜索框"""
        # 淡出动画
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.finished.connect(self._on_hide_finished)
        self.fade_animation.start()
        
    def _on_hide_finished(self):
        """隐藏动画完成"""
        self.setVisible(False)
        self.search_input.clear()
        self.search_closed.emit()
        self.fade_animation.finished.disconnect(self._on_hide_finished)
        
    def _on_text_changed(self, text: str):
        """搜索文本变化"""
        self.clear_btn.setVisible(bool(text))
        self.search_text_changed.emit(text)
        
    def _on_search_confirmed(self):
        """搜索确认"""
        text = self.search_input.text().strip()
        if text:
            self.search_confirmed.emit(text)
            
    def _on_clear(self):
        """清除搜索"""
        self.search_input.clear()
        self.search_input.setFocus()
        
    def keyPressEvent(self, event):
        """按键事件"""
        if event.key() == Qt.Key.Key_Escape:
            self.hide_search()
        else:
            super().keyPressEvent(event)
            
    def get_search_text(self) -> str:
        """获取当前搜索文本"""
        return self.search_input.text().strip()
        
    def set_search_text(self, text: str):
        """设置搜索文本"""
        self.search_input.setText(text)
