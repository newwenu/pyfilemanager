from PySide6.QtWidgets import QDialog, QVBoxLayout, QScrollArea, QWidget, QGridLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

def qt_keys_to_string(keys):
    """将 Qt 键枚举元组转换为用户可读的字符串（如 (AltModifier, Key_Left) → "Alt+Left"）"""
    modifier, key = keys
    modifier_map = {
        Qt.KeyboardModifier.AltModifier: "Alt",
        Qt.KeyboardModifier.ControlModifier: "Ctrl",
        Qt.KeyboardModifier.ShiftModifier: "Shift",
        Qt.KeyboardModifier.NoModifier: ""
    }
    modifier_str = modifier_map.get(modifier, "")
    key_str = Qt.Key(key).name.replace("Key_", "")  # 转换为 "Left" 等可读名称
    return f"{modifier_str}+{key_str}" if modifier_str else key_str

class ShortcutHelpDialog(QDialog):
    def __init__(self, parent=None, shortcuts=None):
        super().__init__(parent)
        self.setWindowTitle("快捷键说明")
        # 修复：添加 Qt.WindowCloseButtonHint 显示关闭按钮
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
        self.setFixedSize(400, 500)  # 固定尺寸
        
        main_layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)  # 允许滚动内容自适应大小

        # 创建容器部件并设置网格布局
        content_widget = QWidget()
        grid_layout = QGridLayout(content_widget)
        grid_layout.setContentsMargins(15, 15, 15, 15)  # 内边距
        grid_layout.setHorizontalSpacing(20)  # 列间距
        grid_layout.setVerticalSpacing(10)    # 行间距

        # 添加表头（说明列和快捷键列）
        title_label = QLabel("常用快捷键说明")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white;")
        grid_layout.addWidget(title_label, 0, 0, 1, 2)  # 跨两列

        # 表头分隔线（可选）
        separator = QLabel()
        separator.setStyleSheet("background: #666; height: 2px;")
        grid_layout.addWidget(separator, 1, 0, 1, 2)

        # 添加列标题
        desc_label = QLabel("功能说明")
        key_label = QLabel("快捷键")
        desc_label.setStyleSheet("color: white; font-weight: bold;")
        key_label.setStyleSheet("color: white; font-weight: bold;")
        grid_layout.addWidget(desc_label, 2, 0)
        grid_layout.addWidget(key_label, 2, 1)

        # 遍历快捷键数据，逐行添加内容
        for row, shortcut in enumerate(shortcuts or [], start=3):  # 从第3行开始
            # 功能说明标签
            desc = QLabel(shortcut["description"])
            desc.setStyleSheet("color: white;")
            desc.setWordWrap(True)  # 长文本换行
            
            # 快捷键标签
            key_str = qt_keys_to_string(shortcut["keys"])
            key = QLabel(key_str)
            key.setStyleSheet("color: white;")
            
            # 添加到网格布局（row行，0列和1列）
            grid_layout.addWidget(desc, row, 0)
            grid_layout.addWidget(key, row, 1)

        # 设置容器部件的最小宽度（避免内容过窄）
        content_widget.setMinimumWidth(360)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

        # 整体背景样式
        self.setStyleSheet("background: rgba(0, 0, 0, 180); border-radius: 8px;")
