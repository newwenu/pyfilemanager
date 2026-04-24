"""
快捷键动作模块 - 定义所有可通过快捷键触发的动作

这些动作通过事件总线触发，而不是直接操作主窗口
"""
from PySide6.QtCore import Qt
from typing import Callable, Optional
from . import event_bus


class ShortcutAction:
    """
    快捷键动作基类
    
    所有快捷键动作都应继承此类
    """
    
    def __init__(self, action_id: str, description: str, 
                 default_keys: tuple = (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_unknown)):
        self.action_id = action_id
        self.description = description
        self.default_keys = default_keys
        self._current_keys = default_keys
    
    @property
    def keys(self) -> tuple:
        """获取当前快捷键"""
        return self._current_keys
    
    def set_keys(self, modifiers: Qt.KeyboardModifier, key: Qt.Key):
        """设置新的快捷键"""
        self._current_keys = (modifiers, key)
    
    def execute(self):
        """执行动作 - 子类必须实现"""
        raise NotImplementedError("子类必须实现execute方法")
    
    def get_description(self, lang: str = "zh_CN") -> str:
        """获取描述（支持多语言）"""
        return self.description


# ========== 导航动作 ==========

class NavigateUpAction(ShortcutAction):
    """返回上级目录"""
    def __init__(self):
        super().__init__(
            "navigate_up",
            "返回上级目录",
            (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_Left)
        )
    
    def execute(self):
        event_bus.navigate_up.emit()


class NavigateHomeAction(ShortcutAction):
    """导航到主页"""
    def __init__(self):
        super().__init__(
            "navigate_home",
            "导航到主页",
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_H)
        )
    
    def execute(self):
        event_bus.navigate_home.emit()


class NavigateRefreshAction(ShortcutAction):
    """刷新界面"""
    def __init__(self):
        super().__init__(
            "navigate_refresh",
            "刷新界面",
            (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_F5)
        )
    
    def execute(self):
        event_bus.navigate_refresh.emit()


# ========== 文件操作动作 ==========

class FileOpenAction(ShortcutAction):
    """打开选中项"""
    def __init__(self):
        super().__init__(
            "file_open",
            "打开选中项",
            (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_Return)
        )
    
    def execute(self):
        event_bus.file_open_selected.emit()


class FileCopyAction(ShortcutAction):
    """复制选中文件"""
    def __init__(self):
        super().__init__(
            "file_copy",
            "复制选中文件",
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_C)
        )
    
    def execute(self):
        # 通过事件总线请求获取选中文件，然后复制
        # 这里简化处理，实际应由主窗口处理
        event_bus.file_copy.emit([])


class FileCutAction(ShortcutAction):
    """剪切选中文件"""
    def __init__(self):
        super().__init__(
            "file_cut",
            "剪切选中文件",
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_X)
        )
    
    def execute(self):
        event_bus.file_cut.emit([])


class FilePasteAction(ShortcutAction):
    """粘贴文件"""
    def __init__(self):
        super().__init__(
            "file_paste",
            "粘贴文件",
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_V)
        )
    
    def execute(self):
        event_bus.file_paste.emit()


class FileDeleteAction(ShortcutAction):
    """删除选中文件"""
    def __init__(self):
        super().__init__(
            "file_delete",
            "删除选中文件",
            (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_Delete)
        )
    
    def execute(self):
        event_bus.file_delete.emit([])


class FileNewFolderAction(ShortcutAction):
    """新建文件夹"""
    def __init__(self):
        super().__init__(
            "file_new_folder",
            "新建文件夹",
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_N)
        )
    
    def execute(self):
        event_bus.file_new_folder.emit("")


class FileRenameAction(ShortcutAction):
    """重命名选中项"""
    def __init__(self):
        super().__init__(
            "file_rename",
            "重命名选中项",
            (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_F2)
        )
    
    def execute(self):
        # 通过事件总线触发重命名操作，由主窗口处理具体逻辑
        # 主窗口的 _on_rename_file 方法会处理实际的对话框和重命名逻辑
        event_bus.file_rename.emit("", "")


# ========== 选择动作 ==========

class SelectAllAction(ShortcutAction):
    """全选文件"""
    def __init__(self):
        super().__init__(
            "select_all",
            "全选文件",
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_A)
        )
    
    def execute(self):
        event_bus.select_all.emit()


# ========== 视图动作 ==========

class ToggleHiddenFilesAction(ShortcutAction):
    """切换隐藏文件显示"""
    def __init__(self):
        super().__init__(
            "toggle_hidden",
            "切换隐藏文件显示",
            (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_unknown)  # 无默认快捷键
        )
    
    def execute(self):
        # 通过事件总线获取当前状态，然后切换
        # 实际由主窗口处理
        pass


class ToggleMTimeAction(ShortcutAction):
    """切换修改时间列显隐"""
    def __init__(self):
        super().__init__(
            "toggle_mtime",
            "切换修改时间列显隐",
            (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_X)
        )
    
    def execute(self):
        event_bus.view_toggle_mtime.emit()


# ========== 焦点动作 ==========

class FocusAddressBarAction(ShortcutAction):
    """聚焦地址栏"""
    def __init__(self):
        super().__init__(
            "focus_address_bar",
            "聚焦地址栏",
            (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_D)
        )
    
    def execute(self):
        event_bus.focus_address_bar.emit()


class FocusFileListAction(ShortcutAction):
    """聚焦文件列表"""
    def __init__(self):
        super().__init__(
            "focus_file_list",
            "聚焦文件列表",
            (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_F)
        )
    
    def execute(self):
        event_bus.focus_file_list.emit()


class FocusNavTreeAction(ShortcutAction):
    """聚焦导航树"""
    def __init__(self):
        super().__init__(
            "focus_nav_tree",
            "聚焦导航树",
            (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_N)
        )
    
    def execute(self):
        event_bus.focus_nav_tree.emit()


# ========== 搜索动作 ==========

class ShowSearchAction(ShortcutAction):
    """显示搜索输入框"""
    def __init__(self):
        super().__init__(
            "show_search",
            "显示搜索输入框",
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_F)
        )
    
    def execute(self):
        event_bus.focus_search_box.emit()


# ========== 应用动作 ==========

class ShowSettingsAction(ShortcutAction):
    """打开设置对话框"""
    def __init__(self):
        super().__init__(
            "show_settings",
            "打开设置对话框",
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_Comma)
        )
    
    def execute(self):
        event_bus.app_show_settings.emit()


class ShowHelpAction(ShortcutAction):
    """打开/关闭快捷键帮助对话框"""
    def __init__(self):
        super().__init__(
            "show_help",
            "打开/关闭快捷键帮助对话框",
            (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_F1)
        )
    
    def execute(self):
        event_bus.app_show_help.emit()


class SwitchLanguageAction(ShortcutAction):
    """切换语言"""
    def __init__(self):
        super().__init__(
            "switch_language",
            "切换语言",
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_L)
        )
    
    def execute(self):
        # 语言切换需要知道当前语言，由主窗口处理
        pass


# ========== 动作注册表 ==========

class ShortcutActionRegistry:
    """
    快捷键动作注册表
    
    管理所有可用的快捷键动作
    """
    
    def __init__(self):
        self._actions: dict[str, ShortcutAction] = {}
        self._register_default_actions()
    
    def _register_default_actions(self):
        """注册默认动作"""
        actions = [
            # 导航
            NavigateUpAction(),
            NavigateHomeAction(),
            NavigateRefreshAction(),
            
            # 文件操作
            FileOpenAction(),
            FileCopyAction(),
            FileCutAction(),
            FilePasteAction(),
            FileDeleteAction(),
            FileNewFolderAction(),
            FileRenameAction(),
            
            # 选择
            SelectAllAction(),
            
            # 视图
            ToggleMTimeAction(),
            
            # 焦点
            FocusAddressBarAction(),
            FocusFileListAction(),
            FocusNavTreeAction(),
            
            # 搜索
            ShowSearchAction(),
            
            # 应用
            ShowSettingsAction(),
            ShowHelpAction(),
            SwitchLanguageAction(),
        ]
        
        for action in actions:
            self.register(action)
    
    def register(self, action: ShortcutAction):
        """注册动作"""
        self._actions[action.action_id] = action
    
    def get(self, action_id: str) -> Optional[ShortcutAction]:
        """获取动作"""
        return self._actions.get(action_id)
    
    def get_all(self) -> list[ShortcutAction]:
        """获取所有动作"""
        return list(self._actions.values())
    
    def execute(self, action_id: str):
        """执行指定动作"""
        action = self._actions.get(action_id)
        if action:
            action.execute()


# 全局注册表实例
action_registry = ShortcutActionRegistry()
