from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, QParallelAnimationGroup, QPropertyAnimation, QRect, QEasingCurve, QAbstractAnimation, QObject
from PySide6.QtGui import QFont, QPainter, QColor, QPalette

from core import event_bus


class CollapsibleSection(QWidget):
    """可折叠区域组件
    
    支持主题切换，自动适应深色/浅色主题
    """
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        
        self.toggle_animation = None
        self.content_area = None
        self.main_layout = None
        self.toggle_button = None
        self.content_layout = None
        self._title = title
        self._theme_connection = None
        
        self._init_ui(title)
        self._setup_theme_aware()
        
    def _init_ui(self, title):
        # 创建切换按钮
        self.toggle_button = QPushButton()
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                border: none;
                text-align: left;
                padding: 10px 12px;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px 6px 0 0;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            QPushButton:checked {
                border-radius: 6px 6px 0 0;
            }
        """)
        
        # 设置标题
        self.toggle_button.setText(f"▶ {title}")
        self.toggle_button.clicked.connect(self._on_toggle)
        
        # 创建内容区域
        self.content_area = QFrame()
        self.content_area.setStyleSheet("""
            QFrame {
                border: none;
                border-radius: 0 0 6px 6px;
            }
        """)
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)
        
        # 创建内容布局
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(8)
        
        # 创建主布局
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(2)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.toggle_button)
        self.main_layout.addWidget(self.content_area)
        self.setLayout(self.main_layout)
        
        # 创建动画
        self.toggle_animation = QParallelAnimationGroup(self)
        
        # 内容区域高度动画
        content_animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        content_animation.setDuration(250)
        content_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.toggle_animation.addAnimation(content_animation)
        
        # 内容区域最小高度动画
        min_height_animation = QPropertyAnimation(self.content_area, b"minimumHeight")
        min_height_animation.setDuration(250)
        min_height_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.toggle_animation.addAnimation(min_height_animation)
        
    def _setup_theme_aware(self):
        """设置主题感知"""
        def on_theme_changed(theme: str, sys_bg_rgb: tuple):
            # 检查对象是否还存在
            if not self or not self.toggle_button:
                return
            try:
                self._update_theme_style(theme, sys_bg_rgb)
            except RuntimeError:
                # 对象已被删除，断开连接
                pass
        
        self._theme_connection = on_theme_changed
        event_bus.theme_changed.connect(on_theme_changed)
        
        # 立即应用当前主题
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPalette
        sys_bg = QApplication.palette().color(QPalette.ColorRole.Window)
        r, g, b, _ = sys_bg.getRgb()
        
        # 尝试获取当前主题
        current_theme = "light"
        parent = self.parent()
        while parent:
            if hasattr(parent, 'theme_manager') and parent.theme_manager:
                current_theme = parent.theme_manager.get_actual_theme()
                break
            parent = parent.parent()
        
        self._update_theme_style(current_theme, (r, g, b))
    
    def _update_theme_style(self, theme: str, sys_bg_rgb: tuple):
        """更新主题样式 - 使用标准调色板颜色"""
        # 检查对象是否还存在
        if not self or not self.toggle_button or not self.content_area:
            return

        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPalette

        # 使用应用程序调色板的标准颜色
        palette = QApplication.palette()
        base_color = palette.color(QPalette.ColorRole.Base)
        button_color = palette.color(QPalette.ColorRole.Button)
        highlight_color = palette.color(QPalette.ColorRole.Highlight)
        text_color = palette.color(QPalette.ColorRole.Text)
        window_color = palette.color(QPalette.ColorRole.Window)

        # 转换为CSS颜色字符串
        def to_css(color):
            return f"rgb({color.red()}, {color.green()}, {color.blue()})"

        text_css = to_css(text_color)
        window_css = to_css(window_color)
        button_css = to_css(button_color)
        highlight_css = to_css(highlight_color)

        # 计算边框颜色（基于文本颜色的半透明版本）
        border_color = f"rgba({text_color.red()}, {text_color.green()}, {text_color.blue()}, 50)"

        # 根据背景亮度决定悬停文字颜色
        brightness = (button_color.red() * 299 + button_color.green() * 587 + button_color.blue() * 114) / 1000
        hover_text_color = "black" if brightness > 128 else "white"

        self.toggle_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {button_css};
                color: {text_css};
                border: 1px solid {border_color};
                border-radius: 6px 6px 0 0;
                text-align: left;
                padding: 10px 12px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {highlight_css};
                color: {hover_text_color};
            }}
            QPushButton:checked {{
                background-color: {window_css};
                border-radius: 6px 6px 0 0;
            }}
        """)

        self.content_area.setStyleSheet(f"""
            QFrame {{
                background-color: {window_css};
                border: 1px solid {border_color};
                border-top: none;
                border-radius: 0 0 6px 6px;
            }}
        """)
        
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
            elif child.layout():
                # 递归清除布局中的内容
                while child.layout().count():
                    inner_child = child.layout().takeAt(0)
                    if inner_child.widget():
                        inner_child.widget().deleteLater()
                child.layout().deleteLater()
                
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
    
    def closeEvent(self, event):
        """关闭时断开事件连接"""
        if self._theme_connection:
            try:
                event_bus.theme_changed.disconnect(self._theme_connection)
            except:
                pass
        super().closeEvent(event)
