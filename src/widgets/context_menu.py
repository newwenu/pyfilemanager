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
        open_in_explorer_action = menu.addAction(main_window.translation.get("open_in_explorer", "在资源管理器打开"))
        new_folder_action = menu.addAction(main_window.translation.get("new_folder", "新建文件夹"))
        new_folder_action.triggered.connect(lambda: handle_new_folder(main_window))
        delete_action.triggered.connect(lambda: handle_delete_file(main_window))
        prop_action.triggered.connect(lambda: FilePropertiesDialog.show_for_selected_item(main_window))
        open_in_explorer_action.triggered.connect(lambda: handle_open_in_explorer(main_window))
    else:
        # 无选中项时显示新建文件夹和打开当前目录选项
        new_folder_action = menu.addAction(main_window.translation.get("new_folder", "新建文件夹"))
        open_current_dir_action = menu.addAction(main_window.translation.get("open_in_explorer", "在资源管理器打开"))
        new_folder_action.triggered.connect(lambda: handle_new_folder(main_window))
        open_current_dir_action.triggered.connect(lambda: handle_open_current_directory(main_window))
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

def handle_open_in_explorer(main_window):
    """处理在资源管理器打开操作"""
    import os
    import subprocess
    from PySide6.QtWidgets import QMessageBox
    
    try:
        selected_items = main_window.file_list.selectedItems()
        if not selected_items:
            return
        
        # 获取第一个选中项的完整路径
        item = selected_items[0]
        file_name = item.text(0)  # 获取第一列的文本（文件名）
        file_path = os.path.join(main_window.current_path, file_name)
        
        # 确保路径存在
        if not os.path.exists(file_path):
            QMessageBox.warning(main_window, 
                              main_window.translation.get("error", "错误"), 
                              main_window.translation.get("file_not_found", "文件不存在"))
            return
        
        # 在资源管理器中打开
        if os.name == 'nt':  # Windows
            if os.path.isdir(file_path):
                # 对于文件夹，直接打开文件夹
                subprocess.Popen(['explorer', file_path])
            else:
                # 对于文件，选中文件
                subprocess.Popen(['explorer', '/select,', file_path])
        else:  # macOS 和 Linux
            import platform
            system = platform.system()
            if os.path.isdir(file_path):
                # 对于文件夹，直接打开文件夹
                if system == 'Darwin':  # macOS
                    subprocess.Popen(['open', file_path])
                else:  # Linux
                    subprocess.Popen(['xdg-open', file_path])
            else:
                # 对于文件，打开父目录
                parent_dir = os.path.dirname(file_path)
                if system == 'Darwin':  # macOS
                    subprocess.Popen(['open', parent_dir])
                else:  # Linux
                    subprocess.Popen(['xdg-open', parent_dir])
                
    except Exception as e:
        logger.error(f"在资源管理器打开失败: {str(e)}")
        QMessageBox.critical(main_window, 
                           main_window.translation.get("error", "错误"), 
                           f"{main_window.translation.get('open_in_explorer_failed', '在资源管理器打开失败')}: {str(e)}")

def handle_open_current_directory(main_window):
    """处理在资源管理器打开当前目录操作"""
    import os
    import subprocess
    from PySide6.QtWidgets import QMessageBox
    
    try:
        current_path = main_window.current_path
        
        # 确保路径存在
        if not os.path.exists(current_path):
            QMessageBox.warning(main_window, 
                              main_window.translation.get("error", "错误"), 
                              main_window.translation.get("directory_not_found", "目录不存在"))
            return
        
        # 在资源管理器中打开当前目录
        if os.name == 'nt':  # Windows
            subprocess.Popen(['explorer', current_path])
        else:  # macOS 和 Linux
            import platform
            system = platform.system()
            if system == 'Darwin':  # macOS
                subprocess.Popen(['open', current_path])
            else:  # Linux
                subprocess.Popen(['xdg-open', current_path])
                
    except Exception as e:
        logger.error(f"在资源管理器打开当前目录失败: {str(e)}")
        QMessageBox.critical(main_window, 
                           main_window.translation.get("error", "错误"), 
                           f"{main_window.translation.get('open_in_explorer_failed', '在资源管理器打开失败')}: {str(e)}")

def show_error(main_window, title, msg):
    """错误提示（独立实现）"""
    QMessageBox.critical(main_window, title, msg)
    logger.error(f"{title}: {msg}")