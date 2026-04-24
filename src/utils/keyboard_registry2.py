from PySide6.QtCore import Qt
from handlers.m_event_handlers import on_tree_select  # 导入
from PySide6.QtWidgets import QMessageBox
import json
from pathlib import Path
import sys
import os

# 导入事件总线和配置提供者
from core import event_bus, config_provider

# 辅助函数：加载用户自定义快捷键配置
def load_user_shortcuts():
    """加载用户自定义快捷键配置"""
    # 检查系统类型
    if sys.platform == "win32":
        load_path = "userdata/config/shortcutswindows.json"
    else:
        load_path = "userdata/config/shortcutslinux.json"
    user_shortcuts_path = Path(load_path)
    if not user_shortcuts_path.exists():
        return []
    try:
        with open(user_shortcuts_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("shortcuts", [])
    except Exception as e:
        print(f"错误：加载用户快捷键配置失败 - {e}")
        return []
    
    # 辅助函数：将modifiers字符串解析为Qt枚举（支持组合键）
def parse_modifiers(modifiers_str: str) -> Qt.KeyboardModifier:
    modifier_mapping = {
        "AltModifier": Qt.KeyboardModifier.AltModifier,
        "ControlModifier": Qt.KeyboardModifier.ControlModifier,
        "ShiftModifier": Qt.KeyboardModifier.ShiftModifier,
        "NoModifier": Qt.KeyboardModifier.NoModifier
    }
    modifiers = Qt.KeyboardModifier.NoModifier
    for part in modifiers_str.split("+"):
        if part in modifier_mapping:
            modifiers |= modifier_mapping[part]
    return modifiers

# 新增：定义默认快捷键配置列表（使用事件总线）
default_shortcuts = [
    # 高频导航操作（用户最常用）
    {
        "id":"1",
        "keys": (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_Left),
        "callback": lambda main_window: lambda: event_bus.navigate_up.emit(),
        "target_widget": None,
        "description": "返回上级目录"
    },
    {
        "id":"2",
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_H),
        "callback": lambda main_window: lambda: event_bus.navigate_home.emit(),
        "target_widget": None,
        "description": "导航到主页"
    },

    # 文件核心操作（打开/复制/剪切/粘贴/删除）
    {
        "keys": (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_Return),
        "callback": lambda main_window: lambda: event_bus.file_open_selected.emit(),
        "target_widget": lambda main_window: main_window.file_list,
        "description": "打开选中项（文件列表）"
    },
    {
        "keys": (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_Return),
        "callback": lambda main_window: lambda: (
            on_tree_select(main_window, main_window.nav_tree.currentItem(), config_provider.get_all()) 
            if main_window.nav_tree.currentItem() else None
        ),
        "target_widget": lambda main_window: main_window.nav_tree,
        "description": "打开选中项（导航树）"
    },
    {
        "id":"3",
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_C),
        "callback": lambda main_window: lambda: _emit_copy_event(main_window),
        "target_widget": lambda main_window: main_window.file_list,
        "description": "复制选中文件"
    },
    {
        "id":"4",
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_X),
        "callback": lambda main_window: lambda: _emit_cut_event(main_window),
        "target_widget": lambda main_window: main_window.file_list,
        "description": "剪切选中文件"
    },
    {
        "id":"5",
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_V),
        "callback": lambda main_window: lambda: event_bus.file_paste.emit(),
        "target_widget": lambda main_window: main_window.file_list,
        "description": "粘贴文件"
    },
    {
        "id":"6",
        "keys": (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_Delete),
        "callback": lambda main_window: lambda: _emit_delete_event(main_window),
        "target_widget": lambda main_window: main_window.file_list,
        "description": "删除选中文件"
    },

    # 编辑辅助操作（全选/重命名/新建）
    {
        "id":"7",
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_A),
        "callback": lambda main_window: lambda: event_bus.select_all.emit(),
        "target_widget": lambda main_window: main_window.file_list,
        "description": "全选文件"
    },
    {
        "id":"8",
        "keys": (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_F2),
        "callback": lambda main_window: lambda: _emit_rename_event(main_window),
        "target_widget": lambda main_window: main_window.file_list,
        "description": "重命名选中项"
    },
    {
        "id":"9",
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_N),
        "callback": lambda main_window: lambda: event_bus.file_new_folder.emit(""),
        "target_widget": None,
        "description": "新建文件夹"
    },

    # 界面控制操作（刷新/搜索/聚焦/列显隐）
    {
        "id":"10",
        "keys": (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_F5),
        "callback": lambda main_window: lambda: event_bus.navigate_refresh.emit(),
        "target_widget": None,
        "description": "刷新界面"
    },
    {
        "id":"11",
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_F),
        "callback": lambda main_window: lambda: event_bus.focus_search_box.emit(),
        "target_widget": None,
        "description": "显示搜索输入框"
    },
    {
        "id":"12",
        "keys": (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_N),
        "callback": lambda main_window: lambda: event_bus.focus_nav_tree.emit(),
        "target_widget": None,
        "target_p": lambda main_window: main_window.nav_tree,
        "is_focus": True,
        "description": "聚焦导航树"
    },
    {
        "id":"13",
        "keys": (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_F),
        "callback": lambda main_window: lambda: event_bus.focus_file_list.emit(),
        "target_widget": None,
        "target_p": lambda main_window: main_window.file_list,
        "is_focus": True,
        "description": "聚焦文件列表"
    },
    {
        "id":"14",
        "keys": (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_D),
        "callback": lambda main_window: lambda: event_bus.focus_address_bar.emit(),
        "target_widget": None,
        "target_p": lambda main_window: main_window.address_bar,
        "is_focus": True,
        "description": "聚焦地址栏"
    },
    {
        "id":"15",
        "keys": (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_X),
        "callback": lambda main_window: lambda: event_bus.view_toggle_mtime.emit(),
        "target_widget": None,
        "description": "切换修改时间列显隐"
    },

    # 辅助功能（帮助文档）
    {
        "id":"16",
        "keys": (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_F1),
        "callback": lambda main_window: lambda: event_bus.app_show_help.emit(),
        "target_widget": None,
        "description": "打开/关闭快捷键帮助对话框"
    },
    {
        "id":"17",
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_L),
        "callback": lambda main_window: lambda: main_window.language_manager.set_language(
            "en_US" if main_window.language_manager.lang == "zh_CN" else "zh_CN"
        ),
        "target_widget": None,
        "description": "切换语言/switch language（重启生效）"
    },
    {
        "id":"18",
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_Comma),
        "callback": lambda main_window: lambda: event_bus.app_show_settings.emit(),
        "target_widget": None,
        "description": "打开设置对话框"
    }
]


# 辅助函数：发射复制事件
def _emit_copy_event(main_window):
    """获取选中项并发射复制事件"""
    selected_items = main_window.file_list.selectedItems()
    files = []
    for item in selected_items:
        file_name = item.text(0)
        file_path = os.path.join(main_window.current_path, file_name)
        files.append(file_path)
    if files:
        event_bus.file_copy.emit(files)


# 辅助函数：发射剪切事件
def _emit_cut_event(main_window):
    """获取选中项并发射剪切事件"""
    selected_items = main_window.file_list.selectedItems()
    files = []
    for item in selected_items:
        file_name = item.text(0)
        file_path = os.path.join(main_window.current_path, file_name)
        files.append(file_path)
    if files:
        event_bus.file_cut.emit(files)


# 辅助函数：发射删除事件
def _emit_delete_event(main_window):
    """获取选中项并发射删除事件"""
    selected_items = main_window.file_list.selectedItems()
    files = []
    for item in selected_items:
        file_name = item.text(0)
        file_path = os.path.join(main_window.current_path, file_name)
        files.append(file_path)
    if files:
        event_bus.file_delete.emit(files)


# 辅助函数：发射重命名事件
def _emit_rename_event(main_window):
    """获取当前项并发射重命名事件"""
    import os
    current_item = main_window.file_list.currentItem()
    if current_item:
        # 获取文件路径
        file_path = current_item.data(0, Qt.UserRole)
        if not file_path:
            file_path = os.path.join(main_window.current_path, current_item.text(0))
        # 使用事件总线发射重命名事件
        # 注意：重命名需要用户输入新名称，这里先打开对话框
        from PySide6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            main_window, "重命名", "新名称：", text=current_item.text(0)
        )
        if ok and new_name.strip():
            event_bus.file_rename.emit(file_path, new_name.strip())


# 加载用户自定义快捷键并更新默认配置（关键修改）
user_shortcuts = load_user_shortcuts()
for user_sc in user_shortcuts:
    sc_id = user_sc.get("id")
    if not sc_id:
        continue  # 跳过无id的配置
    modifiers_str = user_sc.get("modifiers", "NoModifier")
    key_str = user_sc.get("key")
    # 查找默认配置中对应id的项
    for default_sc in default_shortcuts:
        if default_sc.get("id") == sc_id:
            # 解析modifiers和key为Qt枚举
            modifiers = parse_modifiers(modifiers_str)
            key = getattr(Qt.Key, key_str, None)
            if key is not None:
                default_sc["keys"] = (modifiers, key)  # 仅更新键值，保留原有callback等逻辑
                print(f"成功更新快捷键id={sc_id}的键值为：{modifiers_str}+{key_str}")
            else:
                print(f"警告：无效的key值 {key_str}，跳过id={sc_id}的快捷键更新")
            break

def register_app_shortcuts(keyboard_handler, main_window):  # 新增语言参数
    """通过主窗口实例集中注册快捷键（更易扩展）"""
    # 遍历默认快捷键配置列表完成注册
    lang = main_window.language_manager.lang  # 使用LanguageManager获取当前语言
    # 获取快捷键翻译字典
    shortcut_translations = main_window.language_manager.get_shortcut_translations()
    for shortcut in default_shortcuts:
        # 处理需要延迟获取的部件实例（如target_widget/target_p）
        target_widget = shortcut.get("target_widget")(main_window) if callable(shortcut.get("target_widget")) else shortcut.get("target_widget")
        target_p = shortcut.get("target_p")(main_window) if callable(shortcut.get("target_p")) else shortcut.get("target_p")
        # 处理回调函数（需要绑定main_window实例）
        callback = shortcut["callback"](main_window) if callable(shortcut["callback"]) else shortcut["callback"]
        
        # 根据语言选择描述（中文直接使用原description，其他语言从映射获取）
        if lang != "zh_CN":  # 非中文时使用翻译
            description = shortcut_translations.get(shortcut["description"], shortcut["description"])
        else:
            description = shortcut["description"]  # 默认使用中文
            
        keyboard_handler.register_shortcut(
            shortcut["keys"],
            callback,
            target_widget=target_widget,
            target_p=target_p,
            is_focus=shortcut.get("is_focus", False),
            description=description  # 使用翻译后的描述
        )
