"""
核心模块 - 提供事件总线、接口定义和依赖管理
"""
from .event_bus import EventBus, event_bus
from .config_provider import ConfigProvider, config_provider
from .app_config import AppConfig, app_config
from .service_locator import ServiceLocator, inject, get_service, register_service
from .app_initializer import AppInitializer, InitializationError, InitPhase
from .action_context import ActionContext, FileSelection, Clipboard, action_context
from .event_decorators import (
    on_event,
    emit_event,
    emit_after,
    EventMixin,
)
from .interfaces import FileManagerInterface, ConfigProviderInterface
from .shortcut_actions import (
    ShortcutAction,
    ShortcutActionRegistry,
    action_registry,
    # 导航动作
    NavigateUpAction,
    NavigateHomeAction,
    NavigateRefreshAction,
    # 文件操作动作
    FileOpenAction,
    FileCopyAction,
    FileCutAction,
    FilePasteAction,
    FileDeleteAction,
    FileNewFolderAction,
    FileRenameAction,
    # 选择动作
    SelectAllAction,
    # 视图动作
    ToggleMTimeAction,
    # 焦点动作
    FocusAddressBarAction,
    FocusFileListAction,
    FocusNavTreeAction,
    # 搜索动作
    ShowSearchAction,
    # 应用动作
    ShowSettingsAction,
    ShowHelpAction,
    SwitchLanguageAction,
)

__all__ = [
    # 事件总线
    'EventBus',
    'event_bus',
    # 配置提供者
    'ConfigProvider',
    'config_provider',
    # 应用配置
    'AppConfig',
    'app_config',
    # 服务定位器
    'ServiceLocator',
    'inject',
    'get_service',
    'register_service',
    # 应用初始化器
    'AppInitializer',
    'InitializationError',
    'InitPhase',
    # 事件装饰器
    'on_event',
    'emit_event',
    'emit_after',
    'EventMixin',
    # 接口
    'FileManagerInterface',
    'ConfigProviderInterface',
    # 动作上下文
    'ActionContext',
    'FileSelection',
    'Clipboard',
    'action_context',
    # 快捷键动作
    'ShortcutAction',
    'ShortcutActionRegistry',
    'action_registry',
    'NavigateUpAction',
    'NavigateHomeAction',
    'NavigateRefreshAction',
    'FileOpenAction',
    'FileCopyAction',
    'FileCutAction',
    'FilePasteAction',
    'FileDeleteAction',
    'FileNewFolderAction',
    'FileRenameAction',
    'SelectAllAction',
    'ToggleMTimeAction',
    'FocusAddressBarAction',
    'FocusFileListAction',
    'FocusNavTreeAction',
    'ShowSearchAction',
    'ShowSettingsAction',
    'ShowHelpAction',
    'SwitchLanguageAction',
]
