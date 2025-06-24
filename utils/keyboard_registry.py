from PySide6.QtCore import Qt
from handlers.event_handlers import on_tree_select  # 新增导入

def register_app_shortcuts(keyboard_handler, main_window):
    """通过主窗口实例集中注册快捷键（更易扩展）"""
    # 注册Alt+Left返回上级目录（直接访问主窗口方法）
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_Left),
        main_window.navigate_parent_dir
    )
    # 注册F5刷新界面（直接访问主窗口update_filelist）
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_F5),
        main_window.update_filelist
    )
    # 新增：注册Ctrl+F搜索快捷键（调用搜索处理器的显示方法）
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_F),
        main_window.search_handler._show_search_input  # 通过主窗口访问搜索处理器
    )
    # 注册Enter键快捷键（无修饰键） - 关键修改：替换target_object_name为target_widget
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_Return),
        main_window.file_op_handler.open_selected_item,
        target_widget=main_window.file_list  # 替换为具体部件实例（文件列表）
    )

    # 新增：导航树Enter键进入选中项（关键修改）
    def on_nav_tree_enter():
        current_item = main_window.nav_tree.currentItem()
        if current_item:  # 防御性检查（避免空指针）
            on_tree_select(main_window, current_item, main_window.config_manager.config)
    
    # 导航树Enter键触发 - 关键修改：替换target_object_name为target_widget
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_Return),
        on_nav_tree_enter,  # 使用具名函数
        target_widget=main_window.nav_tree  # 替换为具体部件实例（导航树）
    )
    # 新增无鼠标操作快捷键
    # 1. 新建文件夹（Ctrl+N）
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_N),
        main_window.btn_new_folder.click  # 直接触发新建按钮点击事件
    )

    # 5. 全选文件（Ctrl+A）
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_A),
        main_window.file_list.selectAll  # 调用QTreeWidget的全选方法
    )


    # 3. 复制（Ctrl+C）
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_C),
        lambda: main_window.file_manager3.copy_files(main_window.file_list.selectedItems())
    )

    # 4. 剪切（Ctrl+X）
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_X),
        lambda: main_window.file_manager3.cut_files(main_window.file_list.selectedItems())
    )

    # 5. 粘贴（Ctrl+V）
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_V),
        main_window.file_manager3.paste_files
    )
    from PySide6.QtWidgets import QMessageBox
    # 7. 删除（Del）
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_Delete),
        # 补充完整参数：parent_widget=main_window, current_path=当前路径, update_callback=刷新文件列表, error_callback=错误提示
        lambda: main_window.file_manager.delete_files(
            parent_widget=main_window,
            current_path=main_window.current_path,
            selected_items=main_window.file_list.selectedItems(),
            update_callback=main_window.update_filelist,
            error_callback=lambda title, msg: QMessageBox.critical(main_window, title, msg)
        )
    )

    # 6. 重命名（F2）
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_F2),
        lambda: main_window.file_manager3.rename_item(main_window.file_list.currentItem())
    )
    # Alt+N 聚焦导航树（传递导航树部件和描述）
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_N),
        lambda: main_window.nav_tree.setFocus(),
        target_widget=None,  # 关键修改：设为None表示全局触发
        target_p=main_window.nav_tree,
        is_focus=True,
        description="导航树"  # 描述
    )

    # Alt+F 聚焦文件列表（传递文件列表部件和描述）
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_F),
        lambda: main_window.file_list.setFocus(),
        target_widget=None,  # 关键修改：设为None表示全局触发
        target_p=main_window.file_list,
        is_focus=True,
        description="文件列表"  # 描述
    )
    # 聚焦地址栏（Alt+D）
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_D),
        lambda: main_window.address_bar.setFocus(),
        target_widget=None,  # 关键修改：设为None表示全局触发
        target_p=main_window.address_bar,
        is_focus=True,
        description="地址栏"  # 描述

    )
    # 新增：注册 Ctrl+H 导航到 home 文件夹
    keyboard_handler.register_shortcut(
        (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_H),
        main_window.navigate_home,  # 调用导航方法
        target_widget=None,  # 全局触发
        is_focus=True,
        description="导航到主页"  # 提示文本
    )