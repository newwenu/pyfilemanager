"""
导航事件处理器

处理所有与导航相关的事件：
- 导航到指定路径
- 返回上级目录
- 导航到主页
- 刷新当前目录
"""
import os
from typing import TYPE_CHECKING

from core import app_config, get_service
from core.interfaces import FileManagerInterface
from widgets.drive_list_manager import DriveListManager

if TYPE_CHECKING:
    pass  # 不再需要，因为使用 Protocol


class NavigateHandler:
    """导航事件处理器"""

    def __init__(self, file_manager: FileManagerInterface) -> None:
        self.file_manager: FileManagerInterface = file_manager

    def on_navigate_to(self, path: str) -> None:
        """处理导航到指定路径事件"""
        # 更新面包屑地址栏（如果存在）
        if hasattr(self.file_manager, 'breadcrumb_bar'):
            self.file_manager.breadcrumb_bar.set_path(path)
        
        if path == '此电脑':
            # 处理此电脑导航
            self.file_manager.current_path = '此电脑'
            self.file_manager.last_updated_path = '此电脑'
            # 切换到驱动器列表视图
            if self.file_manager.right_stack and self.file_manager.drive_list:
                self.file_manager.right_stack.setCurrentWidget(self.file_manager.drive_list)
                # 更新驱动器列表
                DriveListManager.update_drive_list(
                    file_list=self.file_manager.drive_list,
                    config=app_config.get_all(),
                    icons=self.file_manager.drive_icons,
                    status_bar=self.file_manager.status_bar,
                    current_path=self.file_manager.current_path,
                    translation=self.file_manager.translation
                )
        elif os.path.exists(path):
            # 处理普通路径导航
            self.file_manager.current_path = path
            self.file_manager.last_updated_path = path
            # 切换到文件列表视图
            if self.file_manager.right_stack and self.file_manager.file_list:
                self.file_manager.right_stack.setCurrentWidget(self.file_manager.file_list)
            # 更新文件列表
            self.file_manager.update_filelist()

    def on_navigate_home(self) -> None:
        """处理导航到主页事件"""
        home_handler = get_service("home_handler")
        if home_handler:
            home_handler.navigate_home()

    def navigate_parent_dir(self) -> None:
        """返回上级目录"""
        if self.file_manager.current_path == '此电脑':
            return
        parent_path = os.path.dirname(self.file_manager.current_path)
        if parent_path != self.file_manager.current_path:
            self.file_manager.current_path = parent_path
            # 更新面包屑地址栏（如果存在）
            if hasattr(self.file_manager, 'breadcrumb_bar'):
                self.file_manager.breadcrumb_bar.set_path(self.file_manager.current_path)
            self.file_manager.update_filelist()
