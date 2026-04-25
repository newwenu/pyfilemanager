"""
优化的文件列表组件 - 集成虚拟滚动和分页加载

兼容原有 FileListWidget 的接口，同时提供高性能实现
"""
from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QHeaderView, 
    QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QIcon
from typing import List, Dict, Optional, Callable
import os

from .virtual_file_list import VirtualFileList, VirtualFileListModel
from .paged_file_list import PagedFileList
from .async_icon_loader import AsyncIconLoader, get_async_icon_loader


class OptimizedFileList(VirtualFileList):
    """
    优化的文件列表组件
    
    基于 VirtualFileList，兼容原有 FileListWidget 的接口
    支持：
    - 虚拟滚动（大目录）
    - 异步图标加载
    - 文件夹大小计算
    - 快捷方式图标
    """
    
    # 原有信号
    item_activated = Signal(QTreeWidgetItem, int)  # 保持兼容
    
    def __init__(self, parent=None, use_virtual: bool = True):
        """
        Args:
            parent: 父窗口
            use_virtual: 是否使用虚拟滚动（False则使用分页加载）
        """
        super().__init__(parent)
        
        # 配置
        self._show_all_sizes = False
        self._icons: Dict[str, QIcon] = {}
        self._translation = {}
        
        # 文件夹大小管理
        self._folder_size_callbacks: Dict[str, Callable] = {}
        self._folder_size_manager = None
        
        # 异步图标加载
        self._async_icon_loader = get_async_icon_loader()
        
        # 连接可见范围变化信号
        self.visible_range_changed.connect(self._on_visible_range_changed)
    
    def set_translation(self, translation: Dict):
        """设置翻译字典"""
        self._translation = translation
    
    def setup_columns(self, show_mtime: bool = False):
        """设置列（兼容原有接口）"""
        self.setColumnCount(3 if show_mtime else 2)
        headers = [
            self._translation.get("name", "名称"),
            self._translation.get("size", "大小")
        ]
        if show_mtime:
            headers.append(self._translation.get("mtime", "修改时间"))
        self.setHeaderLabels(headers)
        
        # 设置列宽
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.setColumnWidth(0, 400)
        self.setColumnWidth(1, 100)
        
        if show_mtime:
            header.setSectionResizeMode(2, QHeaderView.Fixed)
            self.setColumnWidth(2, 150)
    
    def load_files(self, files: List[Dict], icons: Dict,
                   show_all_sizes: bool = False, show_mtime: bool = False):
        """
        加载文件列表（增强版）
        
        Args:
            files: 文件信息列表
            icons: 图标字典
            show_all_sizes: 是否显示所有大小
            show_mtime: 是否显示修改时间
        """
        self._is_updating = True
        
        self._icons = icons
        self._show_all_sizes = show_all_sizes
        self._show_mtime = show_mtime
        
        # 预处理文件信息（添加显示大小）
        processed_files = self._preprocess_files(files)
        
        # 设置数据到模型
        self._model.set_files(processed_files)
        
        # 更新滚动条
        self._update_scrollbar()
        
        # 重置滚动位置
        self.verticalScrollBar().setValue(0)
        
        # 更新可见项
        self._update_visible_items()
        
        self._is_updating = False
        
        # 启动文件夹大小计算
        if show_all_sizes:
            self._start_folder_size_calculation(processed_files)
    
    def _preprocess_files(self, files: List[Dict]) -> List[Dict]:
        """预处理文件信息"""
        from utils.size_utils import format_size
        
        processed = []
        for info in files:
            file_info = info.copy()
            
            # 设置显示大小
            if file_info.get("is_dir"):
                if self._show_all_sizes:
                    file_info["display_size"] = self._translation.get("calculating", "计算中")
                else:
                    file_info["display_size"] = self._translation.get("folder", "<文件夹>")
            else:
                file_info["display_size"] = format_size(file_info.get("size", 0))
            
            # 检查是否为隐藏文件
            file_info["is_hidden"] = self._is_hidden_file(file_info["path"])
            
            processed.append(file_info)
        
        return processed
    
    def _is_hidden_file(self, path: str) -> bool:
        """检查是否为隐藏文件"""
        try:
            if os.name == "nt":
                import win32api
                import win32con
                attrs = win32api.GetFileAttributes(path)
                return attrs & win32con.FILE_ATTRIBUTE_HIDDEN
            else:
                return os.path.basename(path).startswith('.')
        except Exception:
            return False
    
    def _render_items(self, start: int, end: int):
        """渲染项（重写以支持异步图标）"""
        from utils.file_utils import get_file_type
        from utils.size_utils import format_size
        from utils.time_utils import format_mtime_timestamp
        from image_manager.ink_icon import get_shortcut_icon_pixmap
        
        # 保存当前选中项的路径
        selected_paths = self.get_selected_paths()
        
        # 清空并重新创建项
        self.clear()
        
        # 获取可见范围的文件
        files = self._model.get_range(start, end - start)
        
        # 收集需要异步加载图标的文件
        async_icon_paths = []
        
        for i, info in enumerate(files):
            actual_index = start + i
            name = info['name']
            path = info['path']
            is_dir = info.get('is_dir', False)
            file_type = 'folder' if is_dir else get_file_type(name)
            
            # 大小列
            size = info.get("display_size", "")
            
            # 修改时间列
            mtime = ""
            if self._show_mtime and info.get('mtime'):
                mtime = format_mtime_timestamp(info['mtime'])
            
            # 创建项
            item = QTreeWidgetItem([name, size, mtime])
            item.setData(0, Qt.ItemDataRole.UserRole, path)
            
            # 检查是否使用系统图标（按扩展名或default类型）
            from image_manager.icon_settings_manager import get_icon_settings_manager
            icon_settings = get_icon_settings_manager()
            file_ext = os.path.splitext(name)[1].lower()
            use_system_icon_by_ext = icon_settings.is_use_system_icon(file_ext)
            use_system_icon_by_default = (file_type == 'default' and icon_settings.is_use_system_icon_for_default())
            use_system_icon = use_system_icon_by_ext or use_system_icon_by_default

            # 设置图标（先设置默认图标）
            icon = self._icons.get(file_type, self._icons.get('default'))
            if icon:
                item.setIcon(0, icon)

            # 特殊处理快捷方式和使用系统图标的扩展名/default类型
            if file_type == 'shortcut' or use_system_icon:
                async_icon_paths.append(path)
                item.setData(0, Qt.ItemDataRole.UserRole + 1, True)  # 标记需要异步加载
            
            # 隐藏文件灰色显示
            if info.get('is_hidden'):
                item.setForeground(0, QColor(Qt.GlobalColor.gray))
            
            item.setToolTip(0, name)
            self.addTopLevelItem(item)
            
            # 恢复选中状态
            if path in selected_paths:
                item.setSelected(True)
        
        # 设置视口边距
        top_margin = start * self._item_height
        bottom_margin = (self._model.total_count - end) * self._item_height
        self.setViewportMargins(0, top_margin, 0, bottom_margin)
        
        # 异步加载图标
        if async_icon_paths:
            self._load_icons_async(async_icon_paths)
    
    def _load_icons_async(self, paths: List[str]):
        """异步加载图标"""
        for path in paths:
            self._async_icon_loader.load_icon(
                path,
                lambda icon, p=path: self._update_item_icon(p, icon),
                AsyncIconLoader.PRIORITY_VISIBLE
            )
    
    def _update_item_icon(self, path: str, icon: QIcon):
        """更新项图标"""
        # 查找对应的项
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == path:
                item.setIcon(0, icon)
                break
    
    def _on_visible_range_changed(self, start: int, end: int):
        """可见范围变化"""
        # 可以在这里触发文件夹大小计算
        pass
    
    def _start_folder_size_calculation(self, files: List[Dict]):
        """启动文件夹大小计算"""
        from core import get_service
        
        folder_size_manager = get_service("folder_size_manager")
        if not folder_size_manager:
            return
        
        for info in files:
            if info.get("is_dir"):
                path = info["path"]
                # 延迟启动计算，避免阻塞
                QTimer.singleShot(100, lambda p=path: self._calculate_folder_size(p))
    
    def _calculate_folder_size(self, path: str):
        """计算文件夹大小"""
        from core import get_service
        
        folder_size_manager = get_service("folder_size_manager")
        if not folder_size_manager:
            return
        
        # 查找对应的项
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == path:
                # 启动计算
                thread = folder_size_manager.start_calculate(path, item)
                if thread:
                    thread.size_calculated.connect(
                        lambda size, p=path: self._on_folder_size_calculated(p, size)
                    )
                break
    
    def _on_folder_size_calculated(self, path: str, size: str):
        """文件夹大小计算完成"""
        # 更新模型中的数据
        for i, info in enumerate(self._model._filtered_files):
            if info["path"] == path:
                info["display_size"] = size
                break
        
        # 更新可见项
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == path:
                item.setText(1, size)
                break
    
    # ========== 兼容原有接口 ==========
    
    def set_empty_hint(self, text: str):
        """设置空提示（兼容接口）"""
        # VirtualFileList 不需要此接口，但保留兼容
        if not text:
            return
        
        # 如果列表为空，显示提示
        if self._model.total_count == 0:
            # 创建一个特殊的提示项
            item = QTreeWidgetItem([text, "", ""])
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # 不可选中
            item.setForeground(0, QColor(Qt.GlobalColor.gray))
            self.addTopLevelItem(item)
    
    def selected_items_paths(self) -> List[str]:
        """获取选中项路径（兼容接口）"""
        return self.get_selected_paths()
    
    def scroll_to_item_by_path(self, path: str):
        """滚动到指定路径的项"""
        self.scroll_to_file(path)
    
    def update_item_size(self, path: str, size: str):
        """更新项的大小显示"""
        self._on_folder_size_calculated(path, size)


# 工厂函数
def create_optimized_file_list(parent=None, use_virtual: bool = True) -> OptimizedFileList:
    """
    创建优化的文件列表
    
    Args:
        parent: 父窗口
        use_virtual: 是否使用虚拟滚动
    
    Returns:
        OptimizedFileList 实例
    """
    return OptimizedFileList(parent, use_virtual)
