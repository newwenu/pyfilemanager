"""
动作上下文模块 - 为快捷键和菜单动作提供执行上下文

封装了动作执行时需要的各种服务和状态
"""
from typing import List, Optional, Callable, Any
from dataclasses import dataclass, field


@dataclass
class FileSelection:
    """文件选择状态"""
    selected_paths: List[str] = field(default_factory=list)
    current_path: str = ""
    
    def get_selected(self) -> List[str]:
        """获取选中的文件路径列表"""
        return self.selected_paths
    
    def get_single_selection(self) -> Optional[str]:
        """获取单个选中的文件路径"""
        if len(self.selected_paths) == 1:
            return self.selected_paths[0]
        return None
    
    def has_selection(self) -> bool:
        """是否有选中项"""
        return len(self.selected_paths) > 0
    
    def clear(self):
        """清空选择"""
        self.selected_paths.clear()


@dataclass
class Clipboard:
    """剪贴板状态"""
    CUT = "cut"
    COPY = "copy"
    
    files: List[str] = field(default_factory=list)
    operation: str = ""  # "cut" 或 "copy"
    
    def is_cut(self) -> bool:
        """是否是剪切操作"""
        return self.operation == self.CUT
    
    def is_copy(self) -> bool:
        """是否是复制操作"""
        return self.operation == self.COPY
    
    def has_files(self) -> bool:
        """剪贴板是否有文件"""
        return len(self.files) > 0
    
    def clear(self):
        """清空剪贴板"""
        self.files.clear()
        self.operation = ""
    
    def set_copy(self, files: List[str]):
        """设置复制文件"""
        self.files = files.copy()
        self.operation = self.COPY
    
    def set_cut(self, files: List[str]):
        """设置剪切文件"""
        self.files = files.copy()
        self.operation = self.CUT


class ActionContext:
    """
    动作执行上下文
    
    封装了动作执行时需要的所有服务和状态
    动作通过上下文与系统交互，而不是直接依赖主窗口
    """
    
    def __init__(self):
        # 状态对象
        self.file_selection = FileSelection()
        self.clipboard = Clipboard()
        
        # 服务引用（通过setter注入）
        self._config_provider: Optional[Any] = None
        self._database: Optional[Any] = None
        self._icon_provider: Optional[Any] = None
        
        # 回调函数
        self._update_filelist_callback: Optional[Callable] = None
        self._show_message_callback: Optional[Callable] = None
        self._show_error_callback: Optional[Callable] = None
        
    # ========== 服务注入 ==========
    
    def set_config_provider(self, provider: Any):
        """设置配置提供者"""
        self._config_provider = provider
        
    def set_database(self, database: Any):
        """设置数据库"""
        self._database = database
        
    def set_icon_provider(self, provider: Any):
        """设置图标提供者"""
        self._icon_provider = provider
        
    def set_update_filelist_callback(self, callback: Callable):
        """设置更新文件列表回调"""
        self._update_filelist_callback = callback
        
    def set_show_message_callback(self, callback: Callable):
        """设置显示消息回调"""
        self._show_message_callback = callback
        
    def set_show_error_callback(self, callback: Callable):
        """设置显示错误回调"""
        self._show_error_callback = callback
        
    # ========== 属性访问 ==========
    
    @property
    def config(self) -> Optional[Any]:
        """获取配置提供者"""
        return self._config_provider
    
    @property
    def database(self) -> Optional[Any]:
        """获取数据库"""
        return self._database
    
    @property
    def icons(self) -> Optional[Any]:
        """获取图标提供者"""
        return self._icon_provider
    
    # ========== 便捷方法 ==========
    
    def update_filelist(self):
        """请求更新文件列表"""
        if self._update_filelist_callback:
            self._update_filelist_callback()
            
    def show_message(self, message: str, duration: int = 3000):
        """显示消息"""
        if self._show_message_callback:
            self._show_message_callback(message, duration)
            
    def show_error(self, title: str, message: str):
        """显示错误"""
        if self._show_error_callback:
            self._show_error_callback(title, message)
    
    def get_config_value(self, key: str, default=None):
        """获取配置值"""
        if self._config_provider:
            return self._config_provider.get(key, default)
        return default


# 全局上下文实例（单例）
action_context = ActionContext()
