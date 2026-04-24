from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
import os
from widgets.properties_dialog import FilePropertiesDialog
from widgets.drive_list_manager import DriveListManager
from utils.logging_config import get_logger
from widgets.context_menu import show_context_menu

# 导入事件总线和配置提供者
from core import event_bus, config_provider

logger = get_logger(__name__)


def setup_event_bindings(main_window, config):
    """设置事件绑定（使用事件总线解耦）"""
    # 导航树选择事件
    main_window.nav_tree.itemClicked.connect(
        lambda item: on_tree_select(main_window, item, config_provider.get_all())
    )
    
    # 文件列表右键菜单
    main_window.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    main_window.file_list.customContextMenuRequested.connect(
        lambda pos: show_context_menu(main_window, pos)
    )
    
    # 新建文件夹按钮点击 - 使用事件总线
    main_window.btn_new_folder.clicked.connect(
        lambda: event_bus.file_new_folder.emit("")
    )
    
    # 显示隐藏文件复选框状态变化 - 使用事件总线
    main_window.cb_hidden.stateChanged.connect(
        lambda state: event_bus.view_toggle_hidden.emit(state == Qt.CheckState.Checked.value)
    )
    
    # 显示所有大小复选框状态变化 - 使用事件总线
    main_window.cb_show_sizes.stateChanged.connect(
        lambda state: event_bus.view_toggle_sizes.emit(state == Qt.CheckState.Checked.value)
    )
    
    # 地址栏回车事件
    main_window.address_bar.returnPressed.connect(
        lambda: on_address_change(main_window, config)
    )
    
    # 驱动器列表双击事件
    main_window.drive_list.itemDoubleClicked.connect(
        lambda item, column: on_item_double_click(main_window, item, column)
    )
    
    # 文件列表双击事件
    main_window.file_list.itemDoubleClicked.connect(
        lambda item, column: on_item_double_click(main_window, item, column)
    )


def on_tree_select(main_window, item, config):
    """导航树选择事件（使用事件总线）"""
    path = item.data(0, Qt.UserRole)
    # 使用事件总线导航，主窗口处理具体逻辑
    event_bus.navigate_to.emit(path)


def handle_new_folder(main_window):
    """处理新建文件夹操作（使用事件总线）"""
    # 通过事件总线触发，主窗口处理具体逻辑
    event_bus.file_new_folder.emit("")


def toggle_hidden_files(main_window, state):
    """切换隐藏文件显示（使用事件总线）"""
    event_bus.view_toggle_hidden.emit(state == Qt.CheckState.Checked.value)


def toggle_show_all_sizes(main_window, state):
    """切换显示所有大小（使用事件总线）"""
    event_bus.view_toggle_sizes.emit(state == Qt.CheckState.Checked.value)


def on_address_change(main_window, config):
    """地址栏回车事件（使用事件总线）"""
    text = main_window.address_bar.text()
    
    if text == '此电脑':
        on_tree_select(main_window, main_window.nav_tree.topLevelItem(0), config)
        return
    
    new_path = text
    if text.startswith('home'):
        new_path = main_window.home_handler.home_path
    
    if os.path.exists(new_path):
        # 使用事件总线导航
        event_bus.navigate_to.emit(new_path)
    else:
        # 使用事件总线显示错误
        event_bus.ui_show_error.emit("错误", "路径不存在")


def on_item_double_click(main_window, item, column):
    """双击文件/文件夹处理（使用事件总线）"""
    if main_window.current_path == '此电脑':
        drive_path = item.data(0, Qt.UserRole)
        # 使用事件总线导航
        event_bus.navigate_to.emit(drive_path)
        return
    
    filename = item.text(0)
    path = os.path.normpath(os.path.join(main_window.current_path, filename))
    
    if not os.path.exists(path):
        return
    
    if not os.access(os.path.dirname(path), os.W_OK):
        # 使用事件总线显示状态消息
        event_bus.ui_update_statusbar.emit("无写入权限", 2000)
        return
    
    if os.path.isdir(path):
        # 使用事件总线导航
        event_bus.navigate_to.emit(path)
    else:
        try:
            os.startfile(path)
        except Exception as e:
            # 使用事件总线显示错误
            event_bus.ui_show_error.emit("错误", str(e))


def show_error(main_window, title, msg):
    """错误提示（使用事件总线）"""
    # 优先使用事件总线
    event_bus.ui_show_error.emit(title, msg)
    logger.error(f"{title}: {msg}")
