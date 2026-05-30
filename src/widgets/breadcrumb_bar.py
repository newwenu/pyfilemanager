"""
面包屑地址栏组件

提供面包屑导航和可编辑路径输入功能
支持点击路径段导航和直接编辑路径
"""
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QSpacerItem, QSizePolicy, QMenu)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor


class BreadcrumbBar(QWidget):
    """面包屑地址栏"""
    
    # 信号：路径被点击或编辑完成
    path_clicked = Signal(str)  # 参数：点击的路径段
    path_edited = Signal(str)   # 参数：编辑后的完整路径
    
    def __init__(self, parent=None, translation=None, bg_color=None):
        super().__init__(parent)
        self.translation = translation or {}
        self.bg_color = bg_color or "rgba(255, 255, 255, 20)"
        self.current_path = ""
        self.is_editing = False
        self._setup_ui()
        
    def _setup_ui(self):
        """初始化UI - 紧凑布局"""
        # 不在这里设置固定高度，由外部调用者设置
        
        # 启用样式背景绘制
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # 无内边距，由外部容器控制
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # 垂直居中
        
        # 面包屑容器 - 使用滚动区域支持长路径
        from PySide6.QtWidgets import QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        # 移除所有内边距
        self.scroll_area.setViewportMargins(0, 0, 0, 0)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QScrollArea > QWidget > QWidget {
                padding: 0px;
                margin: 0px;
            }
        """)
        
        self.breadcrumb_container = QWidget()
        # 不固定容器高度，让它自适应父组件
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_container)
        self.breadcrumb_layout.setContentsMargins(0, 0, 0, 0)  # 无内边距
        self.breadcrumb_layout.setSpacing(0)
        self.breadcrumb_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.scroll_area.setWidget(self.breadcrumb_container)
        
        # 路径编辑框（默认隐藏）
        self.path_edit = QLineEdit()
        self.path_edit.setVisible(False)
        # 不固定编辑框高度，让它自适应父组件
        self.path_edit.setMinimumWidth(200)
        self.path_edit.returnPressed.connect(self._on_edit_finished)
        self.path_edit.editingFinished.connect(self._on_edit_finished)
        
        # 添加到主布局 - 面包屑占据主要空间，编辑框默认不占空间
        self.layout.addWidget(self.scroll_area, 1)
        self.layout.addWidget(self.path_edit, 0)  # 编辑框不拉伸
        
        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 设置样式
        self._apply_style()
        
    def _apply_style(self):
        """应用样式 - 使用传入的背景色"""
        self.setStyleSheet(f"""
            BreadcrumbBar {{
                background-color: {self.bg_color};
                border-radius: 3px;
            }}
            QLabel {{
                color: #cccccc;
                padding: 0px 2px;
                font-size: 12px;
                min-height: 16px;
                max-height: 20px;
            }}
            QLabel:hover {{
                color: #ffffff;
                background-color: rgba(255, 255, 255, 30);
                border-radius: 2px;
            }}
            QPushButton {{
                background-color: transparent;
                border: none;
                color: #cccccc;
                padding: 0px 4px;
                font-size: 12px;
                min-height: 16px;
                max-height: 20px;
            }}
            QPushButton:hover {{
                color: #ffffff;
                background-color: rgba(255, 255, 255, 30);
                border-radius: 2px;
            }}
            QLineEdit {{
                background-color: rgba(255, 255, 255, 40);
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 2px;
                color: #ffffff;
                padding: 1px 4px;
                font-size: 12px;
                min-height: 18px;
                max-height: 22px;
            }}
        """)
        
    def set_path(self, path: str):
        """设置当前路径并更新面包屑显示"""
        self.current_path = path
        if not self.is_editing:
            self._update_breadcrumbs()
            
    def _update_breadcrumbs(self):
        """更新面包屑显示"""
        # 清除现有的面包屑
        while self.breadcrumb_layout.count():
            item = self.breadcrumb_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        if self.current_path == "此电脑":
            # 显示"此电脑"
            self._add_crumb("此电脑", "此电脑", is_last=True)
            return
        
        if not self.current_path:
            # 空路径显示提示或保持空白
            empty_label = QLabel(self.translation.get("no_path", "请选择路径"))
            empty_label.setStyleSheet("""
                color: #888888;
                padding: 0px 4px;
                font-size: 12px;
                font-style: italic;
            """)
            empty_label.setFixedHeight(20)
            self.breadcrumb_layout.addWidget(empty_label)
            return
            
        # 分割路径
        if self.current_path == "/" or self.current_path[1:] == ":\\":
            # 根目录 - 显示为 X: 而不是 X:\
            display_name = self.current_path[:2] if ":" in self.current_path else self.current_path
            self._add_crumb(display_name, self.current_path, is_last=True)
            return
            
        # 构建路径段
        parts = []
        # 清理路径：移除末尾的反斜杠，统一使用反斜杠
        clean_path = self.current_path.rstrip("\\").replace("/", "\\")
        
        if ":" in clean_path:
            # Windows 路径
            drive = clean_path[:2]
            parts.append((drive, drive))
            remaining = clean_path[2:].lstrip("\\")  # 移除盘符后的反斜杠
        else:
            remaining = clean_path
            
        if remaining:
            path_so_far = parts[0][1] if parts else ""
            for part in remaining.split("\\"):
                if part:
                    path_so_far = path_so_far + "\\" + part if path_so_far else part
                    parts.append((part, path_so_far))
        
        # 智能截断：如果路径段太多，显示省略号
        max_visible_parts = 4  # 最多显示的路径段数
        if len(parts) > max_visible_parts:
            # 显示：盘符 > ... > 倒数第二段 > 最后一段
            self._add_crumb(parts[0][0], parts[0][1], is_last=False)
            self._add_ellipsis()
            # 显示最后两段
            for i in range(-2, 0):
                idx = len(parts) + i
                if idx > 0:
                    is_last = (i == -1)
                    self._add_crumb(parts[idx][0], parts[idx][1], is_last)
        else:
            # 添加所有面包屑段
            for i, (name, full_path) in enumerate(parts):
                is_last = (i == len(parts) - 1)
                self._add_crumb(name, full_path, is_last)
                
    def _add_ellipsis(self):
        """添加省略号"""
        sep = QLabel(" > ")
        sep.setStyleSheet("color: #aaaaaa; padding: 0px 1px; font-size: 11px;")
        sep.setFixedHeight(20)
        self.breadcrumb_layout.addWidget(sep)
        
        ellipsis = QLabel("...")
        ellipsis.setStyleSheet("color: #aaaaaa; padding: 0px 2px; font-size: 12px;")
        ellipsis.setFixedHeight(20)
        self.breadcrumb_layout.addWidget(ellipsis)
        
        sep2 = QLabel(" > ")
        sep2.setStyleSheet("color: #aaaaaa; padding: 0px 1px; font-size: 11px;")
        sep2.setFixedHeight(20)
        self.breadcrumb_layout.addWidget(sep2)
            
    def _add_crumb(self, name: str, full_path: str, is_last: bool = False):
        """添加一个面包屑段"""
        # 添加分隔符（除了第一个）
        if self.breadcrumb_layout.count() > 0:
            sep = QLabel(" > ")
            sep.setStyleSheet("color: #aaaaaa; padding: 0px 1px; font-size: 11px;")
            sep.setFixedHeight(20)
            self.breadcrumb_layout.addWidget(sep)
            
        # 创建可点击的路径段
        if is_last:
            # 最后一段使用标签样式
            crumb = QLabel(name)
            crumb.setStyleSheet("""
                color: #ffffff;
                font-weight: bold;
                padding: 0px 3px;
                font-size: 12px;
            """)
            crumb.setFixedHeight(20)
        else:
            # 前面的段使用按钮样式
            crumb = QPushButton(name)
            crumb.setFlat(True)
            crumb.setFixedHeight(20)
            crumb.setCursor(Qt.CursorShape.PointingHandCursor)
            crumb.clicked.connect(lambda checked, p=full_path: self._on_crumb_clicked(p))
            
        self.breadcrumb_layout.addWidget(crumb)
        
    def _on_crumb_clicked(self, path: str):
        """面包屑段被点击"""
        self.path_clicked.emit(path)
        
    def _on_edit_finished(self):
        """路径编辑完成"""
        new_path = self.path_edit.text().strip()
        self.is_editing = False
        # 恢复布局
        self.layout.setStretch(0, 1)  # 滚动区域恢复占据空间
        self.layout.setStretch(1, 0)  # 编辑框不拉伸
        self.scroll_area.setVisible(True)
        self.path_edit.setVisible(False)
        
        if new_path and new_path != self.current_path:
            self.path_edited.emit(new_path)
        else:
            self._update_breadcrumbs()
            
    def start_edit(self):
        """开始编辑路径"""
        self.is_editing = True
        self.path_edit.setText(self.current_path)
        # 隐藏滚动区域，显示编辑框
        self.scroll_area.setVisible(False)
        self.path_edit.setVisible(True)
        # 设置编辑框占据全部空间
        self.layout.setStretch(0, 0)  # 滚动区域不占空间
        self.layout.setStretch(1, 1)  # 编辑框占据全部空间
        self.path_edit.setFocus()
        self.path_edit.selectAll()
        
    def mouseDoubleClickEvent(self, event):
        """双击进入编辑模式"""
        if not self.is_editing:
            self.start_edit()
        super().mouseDoubleClickEvent(event)
        
    def keyPressEvent(self, event):
        """按键事件 - Ctrl+L 聚焦并编辑"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_L:
            self.start_edit()
        else:
            super().keyPressEvent(event)
            
    def focusInEvent(self, event):
        """获得焦点"""
        super().focusInEvent(event)
        
    def get_current_path(self) -> str:
        """获取当前路径"""
        return self.current_path
