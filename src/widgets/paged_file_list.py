"""
分页文件列表组件

解决大目录加载性能问题：
- 分页异步加载，避免UI阻塞
- 渐进式显示，提升用户体验
- 支持中断加载，快速切换目录
"""
from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QHeaderView, 
    QProgressBar, QVBoxLayout, QWidget
)
from PySide6.QtCore import Qt, Signal, QTimer, QObject
from PySide6.QtGui import QColor
from typing import List, Dict, Optional, Callable
import os


class PageLoadManager(QObject):
    """分页加载管理器"""
    
    page_loaded = Signal(int, int)  # 当前页, 总页数
    load_finished = Signal()  # 加载完成
    load_cancelled = Signal()  # 加载被取消
    
    def __init__(self, parent=None, page_size: int = 100):
        super().__init__(parent)
        self._page_size = page_size
        self._all_files: List[Dict] = []
        self._current_page = 0
        self._is_loading = False
        self._is_cancelled = False
        self._timer: Optional[QTimer] = None
    
    def start_load(self, files: List[Dict], callback: Callable[[List[Dict]], None]):
        """开始分页加载
        
        Args:
            files: 完整文件列表
            callback: 每页加载完成后的回调函数
        """
        # 取消之前的加载
        self.cancel_load()
        
        self._all_files = files
        self._current_page = 0
        self._is_loading = True
        self._is_cancelled = False
        self._callback = callback
        
        # 计算总页数
        total_pages = (len(files) + self._page_size - 1) // self._page_size
        
        # 立即加载第一页
        self._load_page()
        
        # 延迟加载后续页面
        if total_pages > 1:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._load_page)
            self._timer.start(50)  # 每50ms加载一页
    
    def _load_page(self):
        """加载当前页"""
        if self._is_cancelled or not self._is_loading:
            return
        
        start = self._current_page * self._page_size
        end = min(start + self._page_size, len(self._all_files))
        
        if start >= len(self._all_files):
            # 加载完成
            self._finish_load()
            return
        
        # 获取当前页数据
        page_files = self._all_files[start:end]
        
        # 调用回调函数
        if self._callback:
            self._callback(page_files)
        
        # 发送进度信号
        total_pages = (len(self._all_files) + self._page_size - 1) // self._page_size
        self.page_loaded.emit(self._current_page + 1, total_pages)
        
        self._current_page += 1
        
        # 检查是否加载完成
        if end >= len(self._all_files):
            self._finish_load()
    
    def _finish_load(self):
        """完成加载"""
        self._is_loading = False
        if self._timer:
            self._timer.stop()
            self._timer = None
        self.load_finished.emit()
    
    def cancel_load(self):
        """取消加载"""
        self._is_cancelled = True
        self._is_loading = False
        if self._timer:
            self._timer.stop()
            self._timer = None
        self.load_cancelled.emit()
    
    @property
    def is_loading(self) -> bool:
        """是否正在加载"""
        return self._is_loading
    
    @property
    def progress(self) -> float:
        """加载进度 (0.0 - 1.0)"""
        if not self._all_files:
            return 1.0
        return min(1.0, (self._current_page * self._page_size) / len(self._all_files))


class PagedFileList(QTreeWidget):
    """分页文件列表控件
    
    特性：
    - 分页加载大目录
    - 显示加载进度
    - 支持取消加载
    """
    
    file_activated = Signal(str)  # 文件被激活（双击/回车）
    
    def __init__(self, parent=None, page_size: int = 100):
        super().__init__(parent)
        
        self._page_size = page_size
        self._load_manager = PageLoadManager(self, page_size)
        self._all_files: List[Dict] = []  # 完整文件列表
        self._loaded_count = 0
        
        # 设置UI
        self._setup_ui()
        
        # 连接信号
        self._load_manager.page_loaded.connect(self._on_page_loaded)
        self._load_manager.load_finished.connect(self._on_load_finished)
        
        # 双击事件
        self.itemDoubleClicked.connect(self._on_item_activated)
    
    def _setup_ui(self):
        """设置UI"""
        self.setColumnCount(3)
        self.setHeaderLabels(["名称", "大小", "修改时间"])
        
        # 设置列宽
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.setColumnWidth(0, 400)
        self.setColumnWidth(1, 100)
        self.setColumnWidth(2, 150)
        
        # 优化性能
        self.setUniformRowHeights(True)
        self.setSelectionMode(QTreeWidget.ExtendedSelection)
    
    def load_files(self, files: List[Dict], icons: Dict, 
                   show_all_sizes: bool = False, show_mtime: bool = False):
        """加载文件列表
        
        Args:
            files: 文件信息列表
            icons: 图标字典
            show_all_sizes: 是否显示所有大小
            show_mtime: 是否显示修改时间
        """
        # 保存参数
        self._all_files = files
        self._icons = icons
        self._show_all_sizes = show_all_sizes
        self._show_mtime = show_mtime
        self._loaded_count = 0
        
        # 清空列表
        self.clear()
        
        # 开始分页加载
        if files:
            self._load_manager.start_load(files, self._on_page_received)
        else:
            self._on_load_finished()
    
    def _on_page_received(self, page_files: List[Dict]):
        """接收到一页数据"""
        from utils.file_utils import get_file_type
        from utils.size_utils import format_size
        from utils.time_utils import format_mtime_timestamp
        from image_manager.icon_manager_factory import get_icon_manager
        
        icon_manager = get_icon_manager()
        
        for info in page_files:
            name = info['name']
            path = info['path']
            is_dir = info.get('is_dir', False)
            
            # 大小列
            if is_dir:
                size = "<文件夹>" if not self._show_all_sizes else "计算中"
            else:
                size = format_size(info.get('size', 0))
            
            # 创建项
            item = QTreeWidgetItem(self, [name, size])
            item.setData(0, Qt.ItemDataRole.UserRole, path)
            
            # 设置图标
            file_type = 'folder' if is_dir else get_file_type(name)
            icon = self._icons.get(file_type, self._icons.get('default'))
            if icon:
                item.setIcon(0, icon)
            
            # 修改时间列
            if self._show_mtime and info.get('mtime'):
                mtime_str = format_mtime_timestamp(info['mtime'])
                item.setText(2, mtime_str)
            
            # 隐藏文件灰色显示
            if info.get('is_hidden'):
                item.setForeground(0, QColor(Qt.GlobalColor.gray))
            
            self._loaded_count += 1
        
        # 刷新显示
        self.viewport().update()
    
    def _on_page_loaded(self, current_page: int, total_pages: int):
        """页面加载进度"""
        # 可以在这里更新状态栏显示加载进度
        pass
    
    def _on_load_finished(self):
        """加载完成"""
        # 更新状态栏
        try:
            from core import event_bus
            event_bus.ui_update_statusbar.emit(
                f"已加载 {self._loaded_count} 个文件", 3000
            )
        except ImportError:
            pass
    
    def cancel_load(self):
        """取消加载"""
        self._load_manager.cancel_load()
    
    def clear(self):
        """清空列表"""
        self.cancel_load()
        super().clear()
        self._all_files = []
        self._loaded_count = 0
    
    def filter_files(self, keyword: str) -> int:
        """过滤文件
        
        Returns:
            匹配的文件数量
        """
        if not keyword:
            # 显示所有
            for i in range(self.topLevelItemCount()):
                self.topLevelItem(i).setHidden(False)
            return self.topLevelItemCount()
        
        match_count = 0
        keyword = keyword.lower()
        
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            name = item.text(0).lower()
            if keyword in name:
                item.setHidden(False)
                match_count += 1
            else:
                item.setHidden(True)
        
        return match_count
    
    def _on_item_activated(self, item: QTreeWidgetItem, column: int):
        """项被激活（双击）"""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path:
            self.file_activated.emit(path)
    
    def get_selected_paths(self) -> List[str]:
        """获取选中的文件路径"""
        paths = []
        for item in self.selectedItems():
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path:
                paths.append(path)
        return paths
