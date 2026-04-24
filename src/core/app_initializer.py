"""
应用初始化器模块 - 负责应用的所有初始化工作

采用分阶段初始化策略，支持：
- 阶段化初始化
- 错误处理
- 初始化日志
- 服务注册
"""
import os
from typing import Any, Callable, Dict, List, Optional
from PySide6.QtWidgets import QMainWindow

from .service_locator import ServiceLocator
from .config_provider import config_provider
from .app_config import app_config
from .event_bus import event_bus
from utils.logging_config import get_logger

logger = get_logger(__name__)


class InitializationError(Exception):
    """初始化错误"""
    pass


class InitPhase:
    """初始化阶段"""
    
    def __init__(self, name: str, init_func: Callable, dependencies: List[str] = None):
        self.name = name
        self.init_func = init_func
        self.dependencies = dependencies or []
        self.completed = False
        self.error = None


class AppInitializer:
    """
    应用初始化器
    
    负责协调应用的完整初始化流程，包括：
    1. 基础配置初始化
    2. 核心服务初始化
    3. UI组件初始化
    4. 功能模块初始化
    5. 事件绑定初始化
    
    使用示例：
        initializer = AppInitializer(main_window, config_manager)
        initializer.initialize()
    """
    
    def __init__(self, main_window: QMainWindow, config_manager: Any):
        """
        初始化应用初始化器
        
        Args:
            main_window: 主窗口实例
            config_manager: 配置管理器
        """
        self.main_window = main_window
        self.config_manager = config_manager
        self.phases: Dict[str, InitPhase] = {}
        self._setup_phases()
    
    def _setup_phases(self):
        """设置初始化阶段"""
        self.phases = {
            "config": InitPhase("config", self._init_config),
            "core": InitPhase("core", self._init_core_services, ["config"]),
            "ui": InitPhase("ui", self._init_ui, ["core"]),
            "modules": InitPhase("modules", self._init_modules, ["ui"]),
            "events": InitPhase("events", self._init_events, ["modules"]),
        }
    
    def initialize(self) -> None:
        """
        执行完整初始化
        
        Raises:
            InitializationError: 如果任何阶段初始化失败
        """
        logger.info("开始应用初始化...")
        
        for phase_name, phase in self.phases.items():
            self._execute_phase(phase)
        
        logger.info("应用初始化完成")
    
    def _execute_phase(self, phase: InitPhase) -> None:
        """
        执行初始化阶段
        
        Args:
            phase: 初始化阶段
        
        Raises:
            InitializationError: 如果初始化失败
        """
        # 检查依赖
        for dep in phase.dependencies:
            if dep in self.phases and not self.phases[dep].completed:
                raise InitializationError(
                    f"阶段 [{phase.name}] 的依赖 [{dep}] 未完成"
                )
        
        try:
            logger.info(f"执行初始化阶段: {phase.name}")
            phase.init_func()
            phase.completed = True
            logger.info(f"初始化阶段 [{phase.name}] 完成")
        except Exception as e:
            phase.error = e
            logger.error(f"初始化阶段 [{phase.name}] 失败: {e}")
            raise InitializationError(f"初始化阶段 [{phase.name}] 失败: {e}") from e
    
    def _init_config(self) -> None:
        """初始化基础配置"""
        # 加载配置到提供者
        config_provider.load(self.config_manager.config)
        
        # 注册到服务定位器
        ServiceLocator.register("config_manager", self.config_manager)
        ServiceLocator.register("config_provider", config_provider)
        ServiceLocator.register("event_bus", event_bus)
        
        # 初始化语言
        from language_manager.language_manager import LanguageManager
        language_manager = LanguageManager(self.main_window, self.config_manager)
        ServiceLocator.register("language_manager", language_manager)
        
        # 初始化错误消息模块（与 LanguageManager 集成）
        from file_operator import error_messages
        error_messages.init_with_language_manager(language_manager)
        
        # 设置主窗口属性
        self.main_window.config_manager = self.config_manager
        self.main_window.language_manager = language_manager
        self.main_window.lang = language_manager.lang
        self.main_window.translation = language_manager.get_translation()
        
        # 状态变量
        self.main_window.sys_bg = None
        self.main_window.last_updated_path = None
        self.main_window.folder_threads = {}
        self.main_window.image_path = app_config.background_image
        
        # 设置启动路径
        start_path = app_config.start_path
        self.main_window.current_path = (
            start_path if os.path.exists(start_path) else os.path.expanduser('~')
        )
        
        # 显示选项
        self.main_window.show_hidden = app_config.show_hidden_files
        self.main_window.show_all_sizes = app_config.show_all_sizes
    
    def _init_core_services(self) -> None:
        """初始化核心服务"""
        # 初始化日志
        from utils.logging_config import init_logging
        init_logging()
        
        # 初始化主题管理器
        from theme_manager.theme_manager import ThemeManager
        theme_manager = ThemeManager(self.main_window)
        theme_manager.theme_changed.connect(self.main_window.on_theme_changed)
        theme_manager.apply_theme(app_config.theme)
        ServiceLocator.register("theme_manager", theme_manager)
        self.main_window.theme_manager = theme_manager
        
        # 初始化图标系统
        self._init_icon_system()
        
        # 初始化数据库 - 使用新的 FileTreeManager 替代 DatabaseManager
        from dbload_manager.file_tree_manager import FileTreeManager
        file_tree_manager = FileTreeManager()
        ServiceLocator.register("file_tree_manager", file_tree_manager)
        self.main_window.file_tree_manager = file_tree_manager
        
        # 保持向后兼容：仍然注册 database 服务（使用 FileTreeManager 包装）
        # 这样其他代码中依赖 db 的模块可以继续工作
        ServiceLocator.register("database", file_tree_manager)
        self.main_window.db = file_tree_manager
    
    def _init_icon_system(self) -> None:
        """初始化图标系统"""
        from image_manager.icon_manager_factory import (
            get_icon_manager, switch_to_new_icon_system
        )
        from image_manager.icon_manager import create_icon_set
        
        try:
            switch_to_new_icon_system()
            icon_manager = get_icon_manager()
            self.main_window.icons = icon_manager.icon_cache
            self.main_window.icon_paths = {}
            for icon_name in self.main_window.icons:
                self.main_window.icon_paths[icon_name] = (
                    icon_manager.config_manager.get_icon_path(icon_name)
                )
        except Exception as e:
            logger.warning(f"新图标系统初始化失败，使用旧系统: {e}")
            self.main_window.icons, self.main_window.icon_paths = create_icon_set(
                "media",
                app_config.file_list_icon_size * 2
            )

        self.main_window.drive_icons, _ = create_icon_set(
            "media",
            app_config.drive_icon_size * 2
        )
        self.main_window.folder_size_index = {}
    
    def _init_ui(self) -> None:
        """初始化UI组件"""
        # 初始化键盘处理器
        from handlers.keyboard_handler import KeyboardHandler
        keyboard_handler = KeyboardHandler(self.main_window)
        ServiceLocator.register("keyboard_handler", keyboard_handler)
        self.main_window.keyboard_handler = keyboard_handler
        
        # UI 初始化
        from widgets.ui_setup import UISetup
        from handlers.m_event_handlers import setup_event_bindings
        
        ui_setup = UISetup(self.main_window, self.config_manager)
        ui_setup.setup_ui()
        setup_event_bindings(self.main_window, app_config.get_all())
        ServiceLocator.register("ui_setup", ui_setup)
        self.main_window.ui_setup = ui_setup
        
        # 初始化文件列表更新器
        from widgets.file_list_updater import FileListUpdater
        file_list_updater = FileListUpdater(self.main_window)
        ServiceLocator.register("file_list_updater", file_list_updater)
        self.main_window.file_list_updater = file_list_updater
        self.main_window.update_filelist()
        
        # 初始化背景管理器
        from image_manager.background_manager import BackgroundManager
        bg_manager = BackgroundManager(
            self.main_window.bg_label,
            self.main_window.image_path,
            random=app_config.start_random
        )
        bg_manager.load_background()
        ServiceLocator.register("bg_manager", bg_manager)
        self.main_window.bg_manager = bg_manager
    
    def _init_modules(self) -> None:
        """初始化功能模块"""
        # 文件夹大小管理器
        from threads.folder_size import FolderSizeManager
        folder_size_manager = FolderSizeManager(self.main_window)
        folder_size_manager.size_updated.connect(
            self.main_window.update_folder_size
        )
        ServiceLocator.register("folder_size_manager", folder_size_manager)
        self.main_window.folder_size_manager = folder_size_manager
        
        # 文件管理器（使用新的 file_operator 模块）
        from file_operator import FileOperator
        from file_operator.ui_adapter import FileOperatorUIAdapter
        
        file_operator = FileOperator()
        file_operator_ui = FileOperatorUIAdapter(file_operator, self.main_window)
        ServiceLocator.register("file_operator", file_operator)
        ServiceLocator.register("file_operator_ui", file_operator_ui)
        self.main_window.file_operator = file_operator
        self.main_window.file_operator_ui = file_operator_ui
        
        # HomeHandler
        from handlers.home_handler import HomeHandler
        home_handler = HomeHandler(self.main_window)
        ServiceLocator.register("home_handler", home_handler)
        self.main_window.home_handler = home_handler
        self.main_window.navigate_home = home_handler.navigate_home
        
        # 搜索处理器
        from handlers.search_handler import SearchHandler
        search_handler = SearchHandler(
            self.main_window,
            self.main_window.file_list_updater
        )
        ServiceLocator.register("search_handler", search_handler)
        self.main_window.search_handler = search_handler
        
        # 文件操作处理器
        from handlers.file_operation import FileOperationHandler
        file_op_handler = FileOperationHandler(self.main_window)
        ServiceLocator.register("file_op_handler", file_op_handler)
        self.main_window.file_op_handler = file_op_handler
        
        # 帮助对话框处理器
        from handlers.help_dialog_handler import HelpDialogHandler
        help_dialog_handler = HelpDialogHandler(self.main_window)
        ServiceLocator.register("help_dialog_handler", help_dialog_handler)
        self.main_window.help_dialog_handler = help_dialog_handler
        
        # 设置对话框管理器
        from widgets.settings.settings_manager import SettingsDialogManager
        settings_manager = SettingsDialogManager.get_instance(
            self.main_window,
            self.config_manager,
            self.main_window.language_manager
        )
        settings_manager.settings_changed.connect(
            self.main_window.on_settings_changed
        )
        ServiceLocator.register("settings_manager", settings_manager)
        self.main_window.settings_manager = settings_manager
        
        # 安装事件过滤器
        keyboard_handler = ServiceLocator.get("keyboard_handler")
        self.main_window.file_list.installEventFilter(keyboard_handler)
        self.main_window.nav_tree.installEventFilter(keyboard_handler)
        self.main_window.installEventFilter(keyboard_handler)
        
        # 设置文件列表
        self.main_window.file_list.setObjectName("file_list")
        from PySide6.QtCore import Qt
        self.main_window.file_list.setAttribute(
            Qt.WidgetAttribute.WA_AcceptTouchEvents, True
        )
        
        # 拖放处理器
        from handlers.drag_drop_handler import DragDropHandler
        drag_drop_handler = DragDropHandler(
            self.main_window.file_list,
            self.main_window
        )
        ServiceLocator.register("drag_drop_handler", drag_drop_handler)
        self.main_window.drag_drop_handler = drag_drop_handler
    
    def _init_events(self) -> None:
        """初始化事件绑定"""
        # 注册快捷键
        from utils.keyboard_registry2 import register_app_shortcuts
        keyboard_handler = ServiceLocator.get("keyboard_handler")
        register_app_shortcuts(keyboard_handler, self.main_window)
        
        # 设置动作上下文
        self._setup_action_context()
    
    def _setup_action_context(self) -> None:
        """设置动作上下文"""
        from .action_context import action_context
        
        action_context.set_config_provider(self.config_manager)
        action_context.set_database(self.main_window.db)
        action_context.set_icon_provider(
            getattr(self.main_window, 'icons', None)
        )
        action_context.set_update_filelist_callback(
            self.main_window.update_filelist
        )
        action_context.set_show_message_callback(
            lambda msg, duration: self.main_window.status_bar.showMessage(
                msg, duration
            )
        )
        action_context.set_show_error_callback(
            lambda title, msg: self.main_window._on_show_error(title, msg)
        )
    
    def get_phase_status(self) -> Dict[str, Dict[str, Any]]:
        """获取各阶段状态"""
        return {
            name: {
                "completed": phase.completed,
                "error": str(phase.error) if phase.error else None
            }
            for name, phase in self.phases.items()
        }
