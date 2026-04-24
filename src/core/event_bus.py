"""
事件总线模块 - 提供中央事件分发机制

使用Qt的Signal/Slot机制实现模块间解耦通信
"""
from PySide6.QtCore import QObject, Signal
from typing import Any, Optional


class EventBus(QObject):
    """
    中央事件总线
    
    所有模块通过事件总线进行通信，而不是直接相互调用
    这大大降低了模块间的耦合度
    """
    
    # ========== 导航事件 ==========
    navigate_to = Signal(str)  # 导航到指定路径
    navigate_up = Signal()  # 返回上级目录
    navigate_home = Signal()  # 导航到主页
    navigate_refresh = Signal()  # 刷新当前目录
    
    # ========== 文件操作事件 ==========
    file_open = Signal(str)  # 打开文件/文件夹
    file_open_selected = Signal()  # 打开选中项
    file_copy = Signal(list)  # 复制文件（传入路径列表）
    file_cut = Signal(list)  # 剪切文件
    file_paste = Signal()  # 粘贴文件
    file_delete = Signal(list)  # 删除文件
    file_rename = Signal(str, str)  # 重命名（旧名，新名）
    file_new_folder = Signal(str)  # 新建文件夹（名称）
    file_properties = Signal(str)  # 显示属性
    
    # ========== 选择事件 ==========
    selection_changed = Signal(list)  # 选择改变（传入选中项列表）
    select_all = Signal()  # 全选
    select_none = Signal()  # 取消选择
    
    # ========== UI更新事件 ==========
    ui_update_filelist = Signal()  # 更新文件列表
    ui_update_navtree = Signal()  # 更新导航树
    ui_update_statusbar = Signal(str, int)  # 更新状态栏（消息，持续时间ms）
    ui_show_message = Signal(str, str)  # 显示消息（类型，消息）
    ui_show_error = Signal(str, str)  # 显示错误（标题，消息）
    ui_show_confirm = Signal(str, str, object)  # 显示确认对话框（标题，消息，回调）
    
    # ========== 视图切换事件 ==========
    view_show_drives = Signal()  # 显示驱动器列表
    view_show_files = Signal()  # 显示文件列表
    view_toggle_hidden = Signal(bool)  # 切换隐藏文件显示
    view_toggle_sizes = Signal(bool)  # 切换显示所有大小
    view_toggle_mtime = Signal()  # 切换修改时间列显示
    
    # ========== 焦点事件 ==========
    focus_address_bar = Signal()  # 聚焦地址栏
    focus_file_list = Signal()  # 聚焦文件列表
    focus_nav_tree = Signal()  # 聚焦导航树
    focus_search_box = Signal()  # 聚焦搜索框
    
    # ========== 搜索事件 ==========
    search_start = Signal(str)  # 开始搜索（关键词）
    search_clear = Signal()  # 清除搜索
    
    # ========== 配置变更事件 ==========
    config_changed = Signal(str, Any)  # 配置改变（键，新值）
    config_reload = Signal()  # 重新加载配置
    
    # ========== 主题事件 ==========
    theme_changed = Signal(str)  # 主题改变（主题名称）
    
    # ========== 语言事件 ==========
    language_changed = Signal(str)  # 语言改变（语言代码）
    
    # ========== 应用事件 ==========
    app_show_settings = Signal()  # 显示设置对话框
    app_show_help = Signal()  # 显示帮助对话框
    app_quit = Signal()  # 退出应用
    
    def __init__(self):
        super().__init__()
        
    def emit_navigate_to(self, path: str):
        """导航到指定路径"""
        self.navigate_to.emit(path)
        
    def emit_status_message(self, message: str, duration: int = 3000):
        """发送状态栏消息"""
        self.ui_update_statusbar.emit(message, duration)
        
    def emit_error(self, title: str, message: str):
        """发送错误消息"""
        self.ui_show_error.emit(title, message)
        
    def emit_config_changed(self, key: str, value: Any):
        """发送配置变更事件"""
        self.config_changed.emit(key, value)


# 全局单例实例
event_bus = EventBus()
