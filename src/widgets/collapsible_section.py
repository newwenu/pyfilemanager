from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, QParallelAnimationGroup, QPropertyAnimation, QRect, QEasingCurve, QAbstractAnimation
from PySide6.QtGui import QFont, QPainter, QColor, QPalette

class CollapsibleSection(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        
        self.toggle_animation = None
        self.content_area = None
        self.main_layout = None
        self.toggle_button = None
        self.content_layout = None
        
        self._init_ui(title)
        
    def _init_ui(self, title):
        # 创建切换按钮
        self.toggle_button = QPushButton()
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: none;
                text-align: left;
                padding: 8px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:checked {
                background-color: #3d3d3d;
            }
        """)
        
        # 设置标题
        self.toggle_button.setText(f"▶ {title}")
        self.toggle_button.clicked.connect(self._on_toggle)
        
        # 创建内容区域
        self.content_area = QFrame()
        self.content_area.setStyleSheet("""
            QFrame {
                background-color: #353535;
                border: none;
                border-top: 1px solid #555;
            }
        """)
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)
        
        # 创建内容布局
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(5)
        
        # 创建主布局
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.toggle_button)
        self.main_layout.addWidget(self.content_area)
        self.setLayout(self.main_layout)
        
        # 创建动画
        self.toggle_animation = QParallelAnimationGroup(self)
        
        # 内容区域高度动画
        content_animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        content_animation.setDuration(200)
        content_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.toggle_animation.addAnimation(content_animation)
        
        # 内容区域最小高度动画
        min_height_animation = QPropertyAnimation(self.content_area, b"minimumHeight")
        min_height_animation.setDuration(200)
        min_height_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.toggle_animation.addAnimation(min_height_animation)
        
    def _on_toggle(self):
        """切换展开/折叠状态"""
        checked = self.toggle_button.isChecked()
        
        # 更新按钮图标
        if checked:
            self.toggle_button.setText(self.toggle_button.text().replace("▶", "▼"))
        else:
            self.toggle_button.setText(self.toggle_button.text().replace("▼", "▶"))
            
        # 设置动画目标高度
        content_height = self.content_layout.sizeHint().height()
        
        if checked:
            # 展开动画
            self.toggle_animation.animationAt(0).setStartValue(0)
            self.toggle_animation.animationAt(0).setEndValue(content_height)
            self.toggle_animation.animationAt(1).setStartValue(0)
            self.toggle_animation.animationAt(1).setEndValue(content_height)
        else:
            # 折叠动画
            self.toggle_animation.animationAt(0).setStartValue(content_height)
            self.toggle_animation.animationAt(0).setEndValue(0)
            self.toggle_animation.animationAt(1).setStartValue(content_height)
            self.toggle_animation.animationAt(1).setEndValue(0)
            
        self.toggle_animation.start()
        
    def setContentLayout(self, content_layout):
        """设置内容布局"""
        # 清除之前的内容
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # 添加新内容
        self.content_layout.addLayout(content_layout)
        
        # 更新内容区域的尺寸策略
        self.content_area.setLayout(self.content_layout)
        
    def expand(self):
        """展开栏目"""
        if not self.toggle_button.isChecked():
            self.toggle_button.setChecked(True)
            self._on_toggle()
            
    def collapse(self):
        """折叠栏目"""
        if self.toggle_button.isChecked():
            self.toggle_button.setChecked(False)
            self._on_toggle()