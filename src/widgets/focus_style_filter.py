from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette
import re

from core import event_bus

class FocusStyleFilter(QObject):
    """焦点样式过滤器
    
    动态获取当前系统背景色，确保主题切换后焦点样式正确
    保留原始透明度设置
    """
    def __init__(self, parent, bg_alpha: int, icon_size: int, is_file_list: bool = False):
        """
        Args:
            parent: 父控件（QTreeWidget）
            bg_alpha: 背景透明度
            icon_size: 图标大小
            is_file_list: 是否是文件列表（影响item样式）
        """
        super().__init__(parent)
        self.parent_widget = parent
        self.bg_alpha = bg_alpha
        self.icon_size = icon_size
        self.is_file_list = is_file_list
        self._is_focused = False
        
        # 订阅主题改变事件
        event_bus.theme_changed.connect(self._on_theme_changed)
    
    def _on_theme_changed(self, theme: str, sys_bg_rgb: tuple):
        """主题改变时更新样式"""
        # 重新应用当前状态的样式
        if self._is_focused:
            self._apply_focus_style(sys_bg_rgb)
        else:
            self._apply_normal_style(sys_bg_rgb)
    
    def _get_style(self, sys_bg_rgb: tuple, border: str = None):
        """生成样式表"""
        r, g, b = sys_bg_rgb
        margin_style = "margin: 0.5px 0;" if self.is_file_list else ""
        style = f"""
            QTreeWidget {{
                background-color: rgba({r}, {g}, {b}, {self.bg_alpha});
                {border if border else ''}
            }}
            QTreeWidget::item {{ 
                height: {self.icon_size}px;
                padding-left: 1px;
                {margin_style}
            }}
        """
        return style
    
    def _apply_normal_style(self, sys_bg_rgb: tuple):
        """应用普通样式"""
        self.parent_widget.setStyleSheet(self._get_style(sys_bg_rgb))
    
    def _apply_focus_style(self, sys_bg_rgb: tuple):
        """应用焦点样式"""
        border = "border: 3px solid #2196F3;"
        self.parent_widget.setStyleSheet(self._get_style(sys_bg_rgb, border))
    
    def _get_current_bg_rgb(self):
        """获取当前系统背景色RGB值"""
        sys_bg = QApplication.palette().color(QPalette.ColorRole.Window)
        r, g, b, _ = sys_bg.getRgb()
        return r, g, b

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn:
            main_window = obj.window()
            if hasattr(main_window, 'keyboard_handler') and main_window.keyboard_handler.is_shortcut_focus:
                # 应用高亮样式
                self._is_focused = True
                self._apply_focus_style(self._get_current_bg_rgb())
                # 应用样式后立即重置标记
                main_window.keyboard_handler.is_shortcut_focus = False
            else:
                # 普通焦点进入
                self._is_focused = True
                self._apply_normal_style(self._get_current_bg_rgb())
        elif event.type() == QEvent.Type.FocusOut:
            self._is_focused = False
            main_window = obj.window()
            # 焦点离开时应用普通样式
            self._apply_normal_style(self._get_current_bg_rgb())
            # 仅当新焦点不在当前窗口内时，才重置is_shortcut_focus
            new_focus = main_window.focusWidget()
            if not new_focus or not main_window.isAncestorOf(new_focus):
                if hasattr(main_window, 'keyboard_handler'):
                    main_window.keyboard_handler.is_shortcut_focus = False
        return super().eventFilter(obj, event)


def install_focus_style_filter(widget, bg_alpha: int, icon_size: int, is_file_list: bool = False):
    """统一安装焦点样式过滤器
    
    Args:
        widget: 要安装过滤器的控件（QTreeWidget）
        bg_alpha: 背景透明度
        icon_size: 图标大小
        is_file_list: 是否是文件列表
    """
    filter_instance = FocusStyleFilter(widget, bg_alpha, icon_size, is_file_list)
    widget.installEventFilter(filter_instance)
    return filter_instance
