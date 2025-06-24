from PySide6.QtCore import QEvent, QObject

class FocusStyleFilter(QObject):
    def __init__(self, parent, initial_style):
        super().__init__(parent)
        self.initial_style = initial_style  # 控件初始样式

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn:
            main_window = obj.window()
            if main_window.keyboard_handler.is_shortcut_focus:
                # 应用高亮样式（继承初始样式+新增边框）
                obj.setStyleSheet(f"""
                    {self.initial_style}
                    QTreeWidget {{
                        border: 3px solid #2196F3;
                        background-color: rgba(0, 0, 0, 180);
                    }}
                """)
                # 关键修改：应用样式后立即重置标记，避免后续误触发
                main_window.keyboard_handler.is_shortcut_focus = False
            else:
                obj.setStyleSheet(self.initial_style)
        elif event.type() == QEvent.Type.FocusOut:
            main_window = obj.window()
            obj.setStyleSheet(self.initial_style)
            # 仅当新焦点不在当前窗口内时，才重置is_shortcut_focus（保留原逻辑）
            new_focus = main_window.focusWidget()
            if not new_focus or not main_window.isAncestorOf(new_focus):
                main_window.keyboard_handler.is_shortcut_focus = False
        return super().eventFilter(obj, event)

def install_focus_style_filter(widget, initial_style):
    """统一安装焦点样式过滤器"""
    filter_instance = FocusStyleFilter(widget, initial_style)
    widget.installEventFilter(filter_instance)
