from PySide6.QtCore import Qt, QObject, QEvent,QPoint
from PySide6.QtWidgets import QLineEdit
from PySide6.QtGui import QKeyEvent
from widgets.shortcut_tip import ShortcutTipWidget  # 导入的提示控件

class KeyboardHandler(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.callbacks = []  # 存储注册的快捷键信息
        self.is_shortcut_focus = False
        self.alt_key_pressed = False  # 记录Alt键是否按下
        self.active_tips = []  # 存储当前显示的提示控件

    def register_shortcut(self, key_combination, callback, target_widget=None,target_p=None, is_focus=False, description=""):
        """
        扩展注册方法，参数：
        - target_widget: 快捷键关联的目标部件（如导航树、文件列表）
        - description: 快捷键描述（如"导航树"）
        """
        self.callbacks.append({
            "keys": key_combination,
            "callback": callback,
            "target_widget": target_widget,
            "target_p": target_p,
            "is_focus": is_focus,
            "description": description
        })

    def handle_event(self, obj, event):
        """处理键盘事件（Alt键状态跟踪）"""
        if event.type() == QKeyEvent.Type.KeyPress:
            # 检测Alt键按下
            if event.key() == Qt.Key.Key_Alt:
                self.alt_key_pressed = True
                self._update_shortcut_tips()  # 显示提示
            for cb in self.callbacks:
                modifiers, key = cb["keys"]
                # 关键修复：将 cb["target"] 改为 cb["target_widget"]，并调整判断逻辑
                if (event.modifiers() == modifiers and 
                    event.key() == key and 
                    (cb["target_widget"] is None or obj == cb["target_widget"])):  # 检查对象是否匹配目标部件
                    if cb["is_focus"]:
                        self.is_shortcut_focus = True
                    cb["callback"]()
                    return True
        elif event.type() == QKeyEvent.Type.KeyRelease:
            # 检测Alt键释放
            if event.key() == Qt.Key.Key_Alt:
                self.alt_key_pressed = False
                self._update_shortcut_tips()  # 隐藏提示
        return False

    def _update_shortcut_tips(self):
        """根据Alt键状态更新提示（显示/隐藏）"""
        # 先清理旧提示
        for tip in self.active_tips:
            tip.hide()
            tip.deleteLater()
        self.active_tips.clear()

        if not self.alt_key_pressed:
            return  # Alt键未按下，无需显示

        main_window = self.parent()
        # ：记录全局快捷键提示的垂直偏移量（初始为0）
        global_tip_offset = 0
        for cb in self.callbacks:
            if cb["is_focus"] and cb["description"]:
                tip = ShortcutTipWidget(main_window)
                tip.set_text(f"{self._key_combination_to_text(cb['keys'])}: {cb['description']}")
                if cb["target_p"]:
                    tip.show_beside(cb["target_p"])  # 有目标部件时显示在其附近（原逻辑）
                else:
                    # 无目标部件时（全局快捷键）：左上角显示，垂直方向累加偏移
                    global_pos = main_window.mapToGlobal(QPoint(0, 0))
                    # 关键修改：每个提示在垂直方向叠加偏移（当前偏移量 + 提示高度 + 间隔）
                    tip.move(global_pos.x() + 10, global_pos.y() + 10 + global_tip_offset)
                    global_tip_offset += tip.height() + 5  # 累加偏移（提示高度+5像素间隔）
                    tip.show()
                self.active_tips.append(tip)

    def _key_combination_to_text(self, key_combination) -> str:
        """将键组合（modifiers, key）转换为文本（如"Alt+N"）"""
        modifiers, key = key_combination
        parts = []
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")
        # 关键修复：移除 decode("utf-8")，直接处理字符串
        key_str = Qt.Key(key).name.replace("Key_", "")  # 如Key_N -> "N"
        if parts:
            return "+".join(parts) + f"+{key_str}"
        return key_str

    def eventFilter(self, obj, event):
        # print(f"[KeyboardHandler] 拦截了事件类型: {event.type().name}")
        """重写事件过滤器，仅处理键盘事件，其他事件传递给默认处理"""
        if isinstance(obj, QLineEdit) and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Alt:
                self.alt_key_pressed = True
                self._update_shortcut_tips()
                return True
        if self.handle_event(obj, event):
            return True
        # 关键修改：仅拦截处理过的事件，其他事件传递给默认处理
        if event.type() == QEvent.TouchUpdate:
            print("[KeyboardHandler] 拦截了 TouchUpdate 事件")  # 调试日志
        return super().eventFilter(obj, event)