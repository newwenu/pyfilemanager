from widgets.help_dialog import ShortcutHelpDialog
from utils.keyboard_registry2 import default_shortcuts

class HelpDialogHandler:
    def __init__(self, main_window):
        self.main_window = main_window
        self.shortcut_help_dialog = None  # 对话框实例
    
    def toggle_dialog(self):
        """统一处理对话框的显示/隐藏逻辑"""
        if self.shortcut_help_dialog is None:
            # 首次创建时传入父窗口和快捷键列表
            self.shortcut_help_dialog = ShortcutHelpDialog(
                parent=self.main_window,
                shortcuts=default_shortcuts
            )
        # 切换可见性
        if self.shortcut_help_dialog.isVisible():
            self.shortcut_help_dialog.hide()
        else:
            self.shortcut_help_dialog.show()
