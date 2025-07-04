import sys
import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem
if True:
    #导入
    from threads.folder_size import FolderSizeManager
    from utils.keyboard_registry2 import register_app_shortcuts,default_shortcuts
    from widgets.file_list_updater import FileListUpdater
    from widgets.ui_setup import setup_ui 
    from handlers.m_event_handlers import setup_event_bindings
    from image_manager.icon_manager import create_icon_set
    from image_manager.background_manager import BackgroundManager
    from Fileoperater.file_manager2 import FileManager2
    from Fileoperater.file_manager3 import FileManager3
    from utils.keyboard_handler import KeyboardHandler
    from dbload_manager.database_manager import DatabaseManager
    from handlers.drag_drop_handler import DragDropHandler  # 导入
    from utils.config_manager import ConfigManager
    from utils.logging_config import init_logging
    from handlers.help_dialog_handler import HelpDialogHandler
    from handlers.file_operation import FileOperationHandler
    from handlers.search_handler import SearchHandler
    # 配置读取逻辑为：
    config_manager = ConfigManager("userdata/config/setting1.json")
    config = config_manager.config



class FileManager(QMainWindow):
    def __init__(self, image_path, config_manager: ConfigManager):  # 依赖注入
        super().__init__()
        self.last_updated_path = None  # ：上次更新的路径
        self.folder_threads = {}  # 用于存储每个文件夹的线程
        self.image_path = image_path
        self.current_path = os.path.expanduser('X:\\')
        self.show_hidden = False  # ：控制是否显示隐藏文件
        self.show_all_sizes = False # ：显示所有大小
        self.config_manager = config_manager  # ：配置管理器
        # 初始化日志（通过配置管理器传递参数）
        init_logging(self.config_manager)
        self.icons, self.icon_paths = create_icon_set("media",self.config_manager.get("file_list_icon_size")*2)  # 使用独立图标管理函数
        self.drive_icons,self.icon_paths = create_icon_set("media",self.config_manager.get("drive_icon_size")*2)
        self.folder_size_index = {}  # ：索引库（路径: 大小）
        # ：初始化 SQLite 数据库
        db_path = "userdata\\db\\folder_size.db"  # 数据库文件路径（可从 config 配置）
        self.db=DatabaseManager(db_path)
        
        # 初始化键盘处理器
        self.keyboard_handler = KeyboardHandler(self)
        setup_ui(self, config)  # UI 初始化（内部创建 toolbar）
        setup_event_bindings(self,config)  # 事件绑定
        # 初始化文件列表更新器
        self.file_list_updater = FileListUpdater(self)
        self.update_filelist()  # 初始加载文件列表
        self.bg_manager = BackgroundManager(self.bg_label, self.image_path)
        self.bg_manager.load_background()
        self.folder_size_manager = FolderSizeManager(self)
        self.folder_size_manager.size_updated.connect(self.update_folder_size)
        # 初始化文件管理器
        self.file_manager = FileManager2()
        self.file_manager3 = FileManager3(self)
        # ：初始化 HomeHandler（模块化处理 home 导航）
        from handlers.home_handler import HomeHandler
        self.home_handler = HomeHandler(self)
        # 将导航方法绑定到主窗口（可选，方便快捷键调用）
        self.navigate_home = self.home_handler.navigate_home
        
        # ：提前初始化搜索处理器
        self.search_handler = SearchHandler(self, self.file_list_updater)
        # ：初始化文件操作处理器
        self.file_op_handler = FileOperationHandler(self)
        # ：初始化帮助对话框处理器
        self.help_dialog_handler = HelpDialogHandler(self)
        # 注册应用级快捷键（此时 search_handler 已初始化）
        register_app_shortcuts(self.keyboard_handler, self)

        # 安装事件过滤器到文件列表
        self.file_list.installEventFilter(self.keyboard_handler)
        self.nav_tree.installEventFilter(self.keyboard_handler)
        self.installEventFilter(self.keyboard_handler)
        
        # 确保文件列表对象名称设置
        self.file_list.setObjectName("file_list")
        # ：启用文件列表的触摸事件接收（确保能响应单指滑动）
        self.file_list.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        # print(f"[Debug] 文件列表触摸支持已启用: {self.file_list.testAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents)}")  # 调试确认
        # 初始化拖放处理器（）
        self.drag_drop_handler = DragDropHandler(self.file_list, self)
        self.shortcut_help_dialog = None



    def resizeEvent(self, event):
        """重写窗口大小变化事件，自动调整背景图片尺寸和悬浮按钮位置"""
        if self.bg_label:
            self.bg_manager.on_window_resized(self.size())
        
        # ：调整悬浮按钮位置（保持右下角）
        if hasattr(self, 'settings_btn'):
            margin = 15  # 按钮与窗口边缘的边距
            btn_width = self.settings_btn.width()
            btn_height = self.settings_btn.height()
            new_x = self.width() - btn_width - margin
            new_y = self.height() - btn_height - margin
            self.settings_btn.move(new_x, new_y)
        
        super().resizeEvent(event)

    def closeEvent(self, event):
        """窗口关闭时清理所有未完成的线程"""
        self.folder_size_manager.stop_all_threads()
        self.db.close()
        # 新增：终止文件列表加载线程
        if hasattr(self.file_list_updater, 'file_list_loader'):
            self.file_list_updater.file_list_loader.stop_all()
        super().closeEvent(event)

    def update_filelist(self):
        """通过更新器触发文件列表更新"""
        if self.current_path == '此电脑':
            return
        self.file_list_updater.update_filelist()
    # ：处理文件夹大小更新的槽函数
    def update_folder_size(self, item: QTreeWidgetItem, size: str):
        """更新文件列表项的大小显示"""
        if item is not None:
            item.setText(1, size)  # 第2列（索引1）显示大小

    def navigate_parent_dir(self):
        """返回上级目录（原按键处理逻辑）"""
        if self.current_path == '此电脑':
            return
        parent_path = os.path.dirname(self.current_path)
        if parent_path != self.current_path:
            self.current_path = parent_path
            self.address_bar.setText(self.current_path)
            self.update_filelist()
        
    # 新增：切换快捷键帮助对话框的显示/隐藏
    def toggle_shortcut_help_dialog(self):
        self.help_dialog_handler.toggle_dialog()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 创建主窗口
    window = FileManager("media/background2.png", config_manager)
    window.show()
    sys.exit(app.exec())
