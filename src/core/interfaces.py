"""
核心接口定义

定义应用中的关键接口，用于解耦组件之间的依赖
"""
from typing import Protocol, Optional, Callable, Any
from PySide6.QtWidgets import QTreeWidget, QStatusBar, QLineEdit, QWidget, QStackedWidget
from PySide6.QtGui import QFont


class FileManagerInterface(Protocol):
    """文件管理器接口
    
    定义文件管理器主窗口需要提供的能力，
    用于解耦事件处理器与具体实现
    """
    
    # ========== 路径相关 ==========
    @property
    def current_path(self) -> str:
        """当前路径"""
        ...
    
    @current_path.setter
    def current_path(self, value: str) -> None:
        ...
    
    @property
    def last_updated_path(self) -> Optional[str]:
        """最后更新的路径"""
        ...
    
    @last_updated_path.setter
    def last_updated_path(self, value: Optional[str]) -> None:
        ...
    
    # ========== UI 控件 ==========
    @property
    def file_list(self) -> QTreeWidget:
        """文件列表控件"""
        ...
    
    @property
    def drive_list(self) -> Optional[QTreeWidget]:
        """驱动器列表控件"""
        ...
    
    @property
    def address_bar(self) -> QLineEdit:
        """地址栏"""
        ...
    
    @property
    def status_bar(self) -> QStatusBar:
        """状态栏"""
        ...
    
    @property
    def right_stack(self) -> Optional[QStackedWidget]:
        """右侧堆叠窗口"""
        ...
    
    @property
    def nav_tree(self) -> Optional[QTreeWidget]:
        """导航树"""
        ...
    
    # ========== 状态属性 ==========
    @property
    def show_hidden(self) -> bool:
        """是否显示隐藏文件"""
        ...
    
    @show_hidden.setter
    def show_hidden(self, value: bool) -> None:
        ...
    
    @property
    def show_all_sizes(self) -> bool:
        """是否显示所有大小"""
        ...
    
    @show_all_sizes.setter
    def show_all_sizes(self, value: bool) -> None:
        ...
    
    # ========== 图标和翻译 ==========
    @property
    def icons(self) -> dict:
        """图标字典"""
        ...
    
    @property
    def drive_icons(self) -> dict:
        """驱动器图标字典"""
        ...
    
    @property
    def translation(self) -> Any:
        """翻译对象"""
        ...
    
    # ========== 更新器 ==========
    @property
    def file_list_updater(self) -> Any:
        """文件列表更新器"""
        ...
    
    # ========== 方法 ==========
    def update_filelist(self) -> None:
        """更新文件列表"""
        ...


class ConfigProviderInterface(Protocol):
    """配置提供者接口"""
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        ...
    
    def get_all(self) -> dict:
        """获取所有配置"""
        ...
