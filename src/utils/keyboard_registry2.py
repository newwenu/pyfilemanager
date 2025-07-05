from PySide6.QtCore import Qt
from handlers.m_event_handlers import on_tree_select  # 导入
from PySide6.QtWidgets import QMessageBox

# 新增：定义默认快捷键配置列表（数据接口）
default_shortcuts = [
    {
        "keys": (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_Left),
        "callback": lambda main_window: main_window.navigate_parent_dir,
        "target_widget": None,
        "description": "返回上级目录"
    },
    {
        "keys": (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_F5),
        "callback": lambda main_window: main_window.update_filelist,
        "target_widget": None,
        "description": "刷新界面"
    },
    {
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_F),
        "callback": lambda main_window: main_window.search_handler._show_search_input,
        "target_widget": None,
        "description": "显示搜索输入框"
    },
    {
        "keys": (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_Return),
        "callback": lambda main_window: main_window.file_op_handler.open_selected_item,
        "target_widget": lambda main_window: main_window.file_list,  # 延迟获取部件实例
        "description": "打开选中项（文件列表）"
    },
    {
        "keys": (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_Return),
        "callback": lambda main_window: lambda: (  # 修正：返回可调用的lambda，而非立即执行
            on_tree_select(main_window, main_window.nav_tree.currentItem(), main_window.config_manager.config) 
            if main_window.nav_tree.currentItem()  # 新增：防御性检查（避免空指针）
            else None
        ),
        "target_widget": lambda main_window: main_window.nav_tree,  # 延迟获取部件实例
        "description": "打开选中项（导航树）"
    },
    {
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_N),
        "callback": lambda main_window: main_window.btn_new_folder.click,
        "target_widget": None,
        "description": "新建文件夹"
    },
    {
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_A),
        "callback": lambda main_window: main_window.file_list.selectAll,
        "target_widget": lambda main_window: main_window.file_list,
        "description": "全选文件"
    },
    {
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_C),
        "callback": lambda main_window: (
            lambda: main_window.file_manager3.copy_files(main_window.file_list.selectedItems())
        ),
        "target_widget": lambda main_window: main_window.file_list,
        "description": "复制选中文件"
    },
    {
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_X),
        "callback": lambda main_window: (
            lambda: main_window.file_manager3.cut_files(main_window.file_list.selectedItems())
        ),
        "target_widget": lambda main_window: main_window.file_list,
        "description": "剪切选中文件"
    },
    {
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_V),
        "callback": lambda main_window: main_window.file_manager3.paste_files,
        "target_widget": lambda main_window: main_window.file_list,
        "description": "粘贴文件"
    },
    {
        "keys": (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_Delete),
        "callback": lambda main_window: (
            lambda: main_window.file_manager.delete_files(
                parent_widget=main_window,
                current_path=main_window.current_path,
                selected_items=main_window.file_list.selectedItems(),
                update_callback=main_window.update_filelist,
                error_callback=lambda title, msg: QMessageBox.critical(main_window, title, msg)
            )
        ),
        "target_widget": lambda main_window: main_window.file_list,
        "description": "删除选中文件"
    },
    {
        "keys": (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_F2),
        "callback": lambda main_window: (
            lambda: main_window.file_manager3.rename_item(main_window.file_list.currentItem())
        ),
        "target_widget": lambda main_window: main_window.file_list,
        "description": "重命名选中项"
    },
    {
        "keys": (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_N),
        "callback": lambda main_window: lambda: main_window.nav_tree.setFocus(),
        "target_widget": None,
        "target_p": lambda main_window: main_window.nav_tree,
        "is_focus": True,
        "description": "聚焦导航树"
    },
    {
        "keys": (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_F),
        "callback": lambda main_window: lambda: main_window.file_list.setFocus(),
        "target_widget": None,
        "target_p": lambda main_window: main_window.file_list,
        "is_focus": True,
        "description": "聚焦文件列表"
    },
    {
        "keys": (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_D),
        "callback": lambda main_window: lambda: main_window.address_bar.setFocus(),
        "target_widget": None,
        "target_p": lambda main_window: main_window.address_bar,
        "is_focus": True,
        "description": "聚焦地址栏"
    },
    {
        "keys": (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_X),
        "callback": lambda main_window: (
            lambda: (
                setattr(main_window.file_list_updater, "show_mtime", not main_window.file_list_updater.show_mtime),
                main_window.file_list_updater.update_filelist()
            )
        ),
        "target_widget": None,
        "description": "切换修改时间列显隐"
    },
    {
        "keys": (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_H),
        "callback": lambda main_window: main_window.navigate_home,
        "target_widget": None,
        "is_focus": True,
        "description": "导航到主页"
    },
    {
        "keys": (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_F1),  # F1键（无修饰符）
        "callback": lambda main_window: main_window.toggle_shortcut_help_dialog,  # 绑定主窗口方法
        "target_widget": None,  # 无特定目标部件
        "description": "打开/关闭快捷键帮助对话框"  # 功能描述
    }
]

def register_app_shortcuts(keyboard_handler, main_window):
    """通过主窗口实例集中注册快捷键（更易扩展）"""
    # 遍历默认快捷键配置列表完成注册
    for shortcut in default_shortcuts:
        # 处理需要延迟获取的部件实例（如target_widget/target_p）
        target_widget = shortcut.get("target_widget")(main_window) if callable(shortcut.get("target_widget")) else shortcut.get("target_widget")
        target_p = shortcut.get("target_p")(main_window) if callable(shortcut.get("target_p")) else shortcut.get("target_p")
        # 处理回调函数（需要绑定main_window实例）
        callback = shortcut["callback"](main_window) if callable(shortcut["callback"]) else shortcut["callback"]
        
        keyboard_handler.register_shortcut(
            shortcut["keys"],
            callback,
            target_widget=target_widget,
            target_p=target_p,
            is_focus=shortcut.get("is_focus", False),
            description=shortcut.get("description", "")
        )