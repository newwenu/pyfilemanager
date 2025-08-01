from PySide6.QtWidgets import QMenu, QMessageBox
from PySide6.QtCore import Qt
from widgets.properties_dialog import FilePropertiesDialog
from utils.logging_config import get_logger
# from handlers.file_manager import FileManager  # 根据实际路径调整导入

logger = get_logger(__name__)

def show_context_menu(main_window, pos):
    """右键菜单显示（独立实现）"""
    item = main_window.file_list.itemAt(pos)
    menu = QMenu(main_window)
    if item:
        # 有选中项时显示删除和属性选项
        delete_action = menu.addAction(main_window.translation.get("delete", "删除"))
        prop_action = menu.addAction(main_window.translation.get("properties", "属性"))
        new_folder_action = menu.addAction(main_window.translation.get("new_folder", "新建文件夹"))
        new_folder_action.triggered.connect(lambda: handle_new_folder(main_window))
        delete_action.triggered.connect(lambda: handle_delete_file(main_window))
        prop_action.triggered.connect(lambda: FilePropertiesDialog.show_for_selected_item(main_window))
    else:
        # 无选中项时显示新建文件夹选项
        new_folder_action = menu.addAction(main_window.translation.get("new_folder", "新建文件夹"))
        new_folder_action.triggered.connect(lambda: handle_new_folder(main_window))
    # 在鼠标位置显示菜单
    menu.exec(main_window.file_list.mapToGlobal(pos))

def handle_new_folder(main_window):
    """处理新建文件夹操作（独立实现）"""
    main_window.file_manager.create_new_folder(
        parent_widget=main_window,
        current_path=main_window.current_path,
        update_callback=main_window.update_filelist,
        error_callback=lambda title, msg: show_error(main_window, title, msg)
    )

def handle_delete_file(main_window):
    """处理删除文件操作（独立实现）"""
    main_window.file_manager.delete_files(
        parent_widget=main_window,
        current_path=main_window.current_path,
        selected_items=main_window.file_list.selectedItems(),
        update_callback=main_window.update_filelist,
        error_callback=lambda title, msg: show_error(main_window, title, msg)
    )

def show_error(main_window, title, msg):
    """错误提示（独立实现）"""
    QMessageBox.critical(main_window, title, msg)
    logger.error(f"{title}: {msg}")
