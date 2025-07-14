from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QMenu  #  QMenu 导入（用于右键菜单）
import os
from widgets.properties_dialog import FilePropertiesDialog  # 属性对话框导入（用于右键菜单的属性操作）
from widgets.drive_list_manager import DriveListManager
from utils.logging_config import get_logger
logger = get_logger(__name__)
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
    main_window.address_bar.returnPressed.connect(lambda: on_address_change(main_window,config))
    # 文件列表双击事件
    # ：绑定驱动器列表的双击事件到 on_item_double_click
    main_window.drive_list.itemDoubleClicked.connect(
        lambda item, column: on_item_double_click(main_window, item, column)
    )
    # ：绑定文件列表的双击事件到 on_item_double_click
    main_window.file_list.itemDoubleClicked.connect(
        lambda item, column: on_item_double_click(main_window, item, column)
    )
    # 新增：文件列表单击事件（处理文件夹展开）
    main_window.file_list.itemClicked.connect(
        lambda item, column: on_item_clicked(main_window, item, column)
    )

def on_item_clicked(main_window, item, column):
    """文件列表项单击处理（添加调试日志）"""
    if column != 0:
        logger.debug(f"非名称列单击（列索引：{column}），忽略")  # 新增列索引日志
        return

    folder_path = item.data(0, Qt.UserRole)
    if not folder_path or not os.path.isdir(folder_path):
        logger.debug(f"非文件夹项单击（路径：{folder_path}），忽略")  # 新增路径验证日志
        return

    # 记录展开状态切换
    if item.isExpanded():
        logger.debug(f"折叠文件夹：{folder_path}")  # 折叠日志
        item.setExpanded(False)
    else:
        if folder_path not in main_window.file_list_updater.loaded_subdirs:
            logger.debug(f"首次展开文件夹，触发子目录加载：{folder_path}")  # 首次加载日志
            main_window.file_list_updater.on_folder_expanded(item)
        logger.debug(f"展开文件夹：{folder_path}")  # 展开日志
        item.setExpanded(True)

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
            current_path=main_window.current_path,
            translation=main_window.translation 
        )
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
    """优化隐藏文件显示：立即刷新并保持当前展开状态"""
    main_window.show_hidden = state == Qt.CheckState.Checked.value
    # 保留当前展开的目录路径
    expanded_paths = [item.data(0, Qt.UserRole) 
                     for item in main_window.file_list.findItems("", Qt.MatchContains) 
                     if item.isExpanded()]
    main_window.update_filelist()
    # 恢复展开状态
    for item in main_window.file_list.findItems("", Qt.MatchContains):
        if item.data(0, Qt.UserRole) in expanded_paths:
            item.setExpanded(True)

def toggle_show_all_sizes(main_window, state):
    """切换显示所有大小"""
    main_window.show_all_sizes = state == Qt.CheckState.Checked.value
    main_window.update_filelist()

def on_address_change(main_window,config):
    """地址栏回车事件"""
    if main_window.address_bar.text() == '此电脑':
        # print(main_window.nav_tree.topLevelItem(0))
        on_tree_select(main_window, main_window.nav_tree.topLevelItem(0), config)
        return
    new_path = main_window.address_bar.text()
    if main_window.address_bar.text().startswith('home'):
        new_path = os.path.join(__file__,"..//..//home")
        new_path = os.path.normpath(new_path)
        # print(new_path)

    if os.path.exists(new_path):
        main_window.current_path = new_path
        main_window.update_filelist()
    else:
        show_error(main_window, "错误", "路径不存在")

# def on_item_double_click(main_window, item, column):
#     """优化双击处理：目录展开/折叠，文件直接打开"""
#     path = item.data(0, Qt.UserRole)  # 从UserRole获取完整路径
#     if not path:
#         return

#     if os.path.isdir(path):
#         # 切换展开状态
#         if item.isExpanded():
#             item.setExpanded(False)
#         else:
#             item.setExpanded(True)
#             # # 异步加载子目录（示例，需结合file_list_loader）
#             # main_window.file_list_updater.load_subdirectory(path, item)
#     else:
#         # 直接打开文件（原有逻辑）
#         os.startfile(path)  # Windows专用，跨平台需调整

def toggle_hidden_files(main_window, state):
    """优化隐藏文件显示：立即刷新并保持当前展开状态"""
    main_window.show_hidden = state == Qt.CheckState.Checked.value
    # 保留当前展开的目录路径
    expanded_paths = [item.data(0, Qt.UserRole) 
                     for item in main_window.file_list.findItems("", Qt.MatchContains) 
                     if item.isExpanded()]
    main_window.update_filelist()
    # 恢复展开状态
    for item in main_window.file_list.findItems("", Qt.MatchContains):
        if item.data(0, Qt.UserRole) in expanded_paths:
            item.setExpanded(True)

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
    logger.error(f"{title}: {msg}")
    print(f"{title}: {msg}")

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
        # show_error(main_window, "错误", f"路径不存在: {path}")
        return
    if not os.access(os.path.dirname(path), os.W_OK):
        # show_error(main_window, "错误", "无写入权限")
        main_window.status_bar.showMessage("无写入权限", 2000)
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

def on_item_clicked(main_window, item, column):
    """文件列表项单击处理（实现文件夹展开）"""
    # 仅处理第一列的单击（名称列）
    if column != 0:
        return

    # 判断是否为文件夹（通过item的UserRole存储的路径是否为目录）
    folder_path = item.data(0, Qt.UserRole)
    if not folder_path or not os.path.isdir(folder_path):
        return  # 非文件夹项，不处理

    # 切换展开状态（展开/折叠）
    if item.isExpanded():
        item.setExpanded(False)
    else:
        # 首次展开时加载子目录（复用已有的展开事件逻辑）
        if folder_path not in main_window.file_list_updater.loaded_subdirs:
            main_window.file_list_updater.async_handler.on_folder_expanded(item)  # 触发子目录加载
        item.setExpanded(True)