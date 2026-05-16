import os
from typing import Optional, Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QTreeWidgetItem
from PySide6.QtGui import QFont

from config_manager.config_manager import ConfigManager

# 导入事件总线、动作上下文和配置
from core import event_bus, action_context, app_config, EventMixin

# 导入事件处理器
from handlers.event_handlers import NavigateHandler, FileOperationHandler, UIHandler


class FileManager(QMainWindow, EventMixin):
    """文件管理器主窗口
    
    使用 AppInitializer 进行分阶段初始化，
    通过 EventMixin 管理事件订阅，
    通过 ServiceLocator 获取服务
    """
    
    def __init__(self, config_manager: ConfigManager) -> None:
        # 初始化 EventMixin
        EventMixin.__init__(self)
        super().__init__()
        
        # 保存配置管理器
        self.config_manager: ConfigManager = config_manager
        
        # 使用 AppInitializer 进行分阶段初始化
        from core import AppInitializer
        initializer = AppInitializer(self, config_manager)
        initializer.initialize()
        
        # 初始化事件处理器
        self._init_handlers()
        
        # 设置事件总线连接
        self._setup_event_bus()
    
    def _init_handlers(self) -> None:
        """初始化事件处理器"""
        self.navigate_handler: NavigateHandler = NavigateHandler(self)
        self.file_op_handler: FileOperationHandler = FileOperationHandler(self)
        self.ui_handler: UIHandler = UIHandler(self)
    
    def _setup_event_bus(self) -> None:
        """设置事件总线连接（使用 EventMixin）"""
        # 导航事件
        self.subscribe("navigate_to", self.navigate_handler.on_navigate_to)
        self.subscribe("navigate_up", self.navigate_handler.navigate_parent_dir)
        self.subscribe("navigate_home", self.navigate_handler.on_navigate_home)
        self.subscribe("navigate_refresh", self.update_filelist)
        
        # 文件操作事件
        self.subscribe("file_open_selected", self.file_op_handler.on_open_selected)
        self.subscribe("file_copy", self.file_op_handler.on_copy_files)
        self.subscribe("file_cut", self.file_op_handler.on_cut_files)
        self.subscribe("file_paste", self.file_op_handler.on_paste_files)
        self.subscribe("file_delete", self.file_op_handler.on_delete_files)
        self.subscribe("file_new_folder", self.file_op_handler.on_new_folder)
        self.subscribe("file_rename", self.file_op_handler.on_rename_file)
        
        # 选择事件
        self.subscribe("select_all", self.file_list.selectAll)
        
        # UI更新事件
        self.subscribe("ui_update_statusbar", self.ui_handler.on_update_statusbar)
        self.subscribe("ui_show_error", self.ui_handler.on_show_error)
        self.subscribe("ui_show_message", self.ui_handler.on_show_message)
        
        # 视图切换事件
        self.subscribe("view_toggle_hidden", self.ui_handler.on_toggle_hidden)
        self.subscribe("view_toggle_sizes", self.ui_handler.on_toggle_sizes)
        self.subscribe("view_toggle_mtime", self.ui_handler.on_toggle_mtime)
        
        # 焦点事件
        self.subscribe("focus_address_bar", self.address_bar.setFocus)
        self.subscribe("focus_file_list", self.file_list.setFocus)
        self.subscribe("focus_nav_tree", self.nav_tree.setFocus)
        
        # 搜索事件
        self.subscribe("search_start", self.ui_handler.on_search_start)
        self.subscribe("search_clear", self.ui_handler.on_search_clear)
        
        # 应用事件
        self.subscribe("app_show_settings", self.ui_handler.show_settings_dialog)
        self.subscribe("app_show_help", self.ui_handler.toggle_shortcut_help_dialog)
    
    def _setup_action_context(self) -> None:
        """设置动作上下文"""
        from core import get_service
        # 注入服务
        action_context.set_config_provider(self.config_manager)
        action_context.set_database(get_service("database"))
        action_context.set_icon_provider(getattr(self, 'icons', None))
        
        # 设置回调
        action_context.set_update_filelist_callback(self.update_filelist)
        action_context.set_show_message_callback(
            lambda msg, duration: self.status_bar.showMessage(msg, duration)
        )
        action_context.set_show_error_callback(
            lambda title, msg: self.ui_handler.on_show_error(title, msg)
        )
    
    def _setup_icon_system(self) -> None:
        """初始化图标系统"""
        from image_manager.icon_manager import create_icon_set

        # 使用旧版图标系统
        self.icons, self.icon_paths = create_icon_set(
            "media",
            app_config.file_list_icon_size * 2
        )
        
        self.drive_icons, self.icon_paths = create_icon_set(
            "media",
            app_config.drive_icon_size * 2
        )
        self.folder_size_index = {}
    
    # ========== 事件处理方法 ==========
    
    def resizeEvent(self, event) -> None:
        """重写窗口大小变化事件"""
        if self.bg_label:
            self.bg_manager.on_window_resized(self.size())
        
        if hasattr(self, 'settings_btn'):
            margin = 15
            btn_width = self.settings_btn.width()
            btn_height = self.settings_btn.height()
            new_x = self.width() - btn_width - margin
            new_y = self.height() - btn_height - margin
            self.settings_btn.move(new_x, new_y)
        
        super().resizeEvent(event)

    def closeEvent(self, event) -> None:
        """窗口关闭时清理"""
        from core import get_service
        self.statusBar().showMessage("正在关闭...")
        folder_size_manager = get_service("folder_size_manager")
        if folder_size_manager:
            folder_size_manager.stop_all_threads()
        database = get_service("database")
        if database:
            database.close()
        if hasattr(self.file_list_updater, 'file_list_loader'):
            self.file_list_updater.file_list_loader.stop_all()
        super().closeEvent(event)

    def on_theme_changed(self, theme: str) -> None:
        """处理主题改变事件"""
        pass

    def on_settings_changed(self, config: dict) -> None:
        """处理设置改变事件

        Args:
            config: 新的配置字典
        """
        # 检查是否需要更新文件夹大小计算线程数
        if "folder_size" in config and "max_threads" in config["folder_size"]:
            try:
                max_threads = config["folder_size"]["max_threads"]
                if hasattr(self, 'folder_size_manager') and self.folder_size_manager:
                    self.folder_size_manager.set_max_threads(max_threads)
                    logger.info(f"已从设置更新文件夹大小计算线程数: {max_threads}")
            except Exception as e:
                logger.error(f"更新线程数设置失败: {e}")

    def update_filelist(self) -> None:
        """更新文件列表"""
        if self.current_path == '此电脑':
            return
        self.file_list_updater.update_filelist()
    
    def update_folder_size(self, item: QTreeWidgetItem, size: str) -> None:
        """更新文件夹大小显示"""
        if item is not None:
            item.setText(1, size)

    def show_settings_tip(self, message: str, duration: int = 2000, tip_type: str = "info") -> None:
        """显示设置提示"""
        from tip_manager.tip_manager_proxy import show_tip
        show_tip(self, message, duration, tip_type)
