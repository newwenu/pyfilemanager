from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QMenu  #  QMenu 导入（用于右键菜单）
import os
from widgets.properties_dialog import FilePropertiesDialog  # 属性对话框导入（用于右键菜单的属性操作）
from widgets.drive_list_manager import DriveListManager

def setup_event_bindings(main_window, config):
    """设置事件绑定（完整实现）"""
    # 导航树选择事件
    main_window.nav_tree.itemClicked.connect(lambda item: on_tree_select(main_window, item, config))
    # 文件列表右键菜单
    main_window.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    main_window.file_list.customContextMenuRequested.connect(lambda pos: show_context_menu(main_window, pos))
    # 新建文件夹按钮点击
    main_window.btn_new_folder.clicked.connect(lambda: handle_new_folder(main_window))
    # 显示隐藏文件复选框状态变化
    main_window.cb_hidden.stateChanged.connect(lambda state: toggle_hidden_files(main_window, state))
    # 显示所有大小复选框状态变化
    main_window.cb_show_sizes.stateChanged.connect(lambda state: toggle_show_all_sizes(main_window, state))
    # 地址栏回车事件
    main_window.address_bar.returnPressed.connect(lambda: on_address_change(main_window))
    # 文件列表双击事件
    # ：绑定驱动器列表的双击事件到 on_item_double_click
    main_window.drive_list.itemDoubleClicked.connect(
        lambda item, column: on_item_double_click(main_window, item, column)
    )
    # ：绑定文件列表的双击事件到 on_item_double_click
    main_window.file_list.itemDoubleClicked.connect(
        lambda item, column: on_item_double_click(main_window, item, column)
    )


def on_tree_select(main_window, item,config):
    """导航树选择事件（完整实现）"""
    path = item.data(0, Qt.UserRole)
    if path == '此电脑':
        main_window.current_path = '此电脑'
        # 切换到驱动器列表并更新内容
        main_window.right_stack.setCurrentWidget(main_window.drive_list)
        DriveListManager.update_drive_list(
            file_list=main_window.drive_list,
            config=config,
            icons=main_window.drive_icons,
            status_bar=main_window.status_bar,
            current_path=main_window.current_path
        )
        # show_drives_in_filelist(main_window,config)  # 已通过导入补充该函数
        main_window.address_bar.setText("此电脑")
        main_window.last_updated_path = '此电脑'
    else:
        main_window.current_path = path
        if main_window.current_path != main_window.last_updated_path:
            
            # 切换回主文件列表并更新
            main_window.right_stack.setCurrentWidget(main_window.file_list)
            main_window.update_filelist()
            main_window.last_updated_path = path
    main_window.address_bar.setText(main_window.current_path)

def show_context_menu(main_window, pos):
    """右键菜单显示（完整实现）"""
    item = main_window.file_list.itemAt(pos)
    menu = QMenu(main_window)
    # 假设属性对话框已实现（需根据实际工程调整导入路径）
    if item:
        # 有选中项时显示删除和属性选项
        delete_action = menu.addAction("删除")
        prop_action = menu.addAction("属性")
        delete_action.triggered.connect(lambda: handle_delete_file(main_window))
        prop_action.triggered.connect(lambda: FilePropertiesDialog.show_for_selected_item(main_window))
    else:
        # 无选中项时显示新建文件夹选项
        new_folder_action = menu.addAction("新建文件夹")
        new_folder_action.triggered.connect(lambda: handle_new_folder(main_window))
    # 在鼠标位置显示菜单
    menu.exec(main_window.file_list.mapToGlobal(pos))

def handle_new_folder(main_window):
    """处理新建文件夹操作"""
    main_window.file_manager.create_new_folder(
        parent_widget=main_window,
        current_path=main_window.current_path,
        update_callback=main_window.update_filelist,
        error_callback=lambda title, msg: show_error(main_window, title, msg)
    )

def toggle_hidden_files(main_window, state):
    """切换隐藏文件显示"""
    main_window.show_hidden = state == Qt.CheckState.Checked.value
    main_window.update_filelist()

def toggle_show_all_sizes(main_window, state):
    """切换显示所有大小"""
    main_window.show_all_sizes = state == Qt.CheckState.Checked.value
    main_window.update_filelist()

def on_address_change(main_window):
    """地址栏回车事件"""
    new_path = main_window.address_bar.text()
    if os.path.exists(new_path):
        main_window.current_path = new_path
        main_window.update_filelist()
    else:
        show_error(main_window, "错误", "路径不存在")

def on_item_double_click(main_window, item, column):
    """双击文件/文件夹处理（完整实现）"""
    if main_window.current_path == '此电脑':
        drive_path = item.data(0, Qt.UserRole)
        # print(f"双击驱动器: {drive_path}")
        main_window.current_path = drive_path
        # ：切换到主文件列表（与 on_tree_select 逻辑一致）
        main_window.right_stack.setCurrentWidget(main_window.file_list)
        main_window.update_filelist()
        main_window.address_bar.setText(drive_path)
        return
    filename = item.text(0)
    path = os.path.normpath(os.path.join(main_window.current_path, filename))

    if not os.path.exists(path):
        show_error(main_window, "错误", f"路径不存在: {path}")
        return
    if not os.access(os.path.dirname(path), os.W_OK):
        show_error(main_window, "错误", "无写入权限")
        return

    if os.path.isdir(path):
        main_window.current_path = path
        main_window.address_bar.setText(path)
        main_window.update_filelist()
        main_window.last_updated_path = path
    else:
        try:
            os.startfile(path)
        except Exception as e:
            show_error(main_window, "错误", str(e))

def handle_delete_file(main_window):
    """处理删除文件操作"""
    main_window.file_manager.delete_files(
        parent_widget=main_window,
        current_path=main_window.current_path,
        selected_items=main_window.file_list.selectedItems(),
        update_callback=main_window.update_filelist,
        error_callback=lambda title, msg: show_error(main_window, title, msg)
    )

def show_error(main_window, title, msg):
    """错误提示"""
    QMessageBox.critical(main_window, title, msg)
    print(f"{title}: {msg}")