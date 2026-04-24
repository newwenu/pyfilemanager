"""
简化版虚拟文件列表 - 稳定可靠

解决大目录加载性能问题：
- 分页加载，避免UI阻塞
- 渐进式显示
- 支持中断
"""
from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QHeaderView, 
    QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor
from typing import List, Dict, Optional
import os
import logging

logger = logging.getLogger(__name__)


class SimpleVirtualFileList(QTreeWidget):
    """
    简化版虚拟文件列表
    
    特性：
    - 分批加载，每批100个
    - 不阻塞UI
    - 支持中断
    """
    
    file_activated = Signal(str)  # 文件被激活
    
    def __init__(self, parent=None, batch_size: int = 100):
        super().__init__(parent)
        
        self._batch_size = batch_size
        self._all_files: List[Dict] = []
        self._loaded_count = 0
        self._icons: Dict = {}
        self._show_all_sizes = False
        self._show_mtime = False
        self._translation = {}
        self._is_loading = False
        
        # 使用 QTimer 对象而不是 singleShot，以便可以取消
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._load_batch_sync)
        
        # 设置UI
        self._setup_ui()
        
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
    
    def set_translation(self, translation: Dict):
        """设置翻译字典"""
        self._translation = translation
    
    def setup_columns(self, show_mtime: bool = False):
        """设置列"""
        self.setColumnCount(3 if show_mtime else 2)
        headers = [
            self._translation.get("name", "名称"),
            self._translation.get("size", "大小")
        ]
        if show_mtime:
            headers.append(self._translation.get("mtime", "修改时间"))
        self.setHeaderLabels(headers)
        
        if not show_mtime:
            self.setColumnHidden(2, True)
    
    def load_files(self, files: List[Dict], icons: Dict,
                   show_all_sizes: bool = False, show_mtime: bool = False):
        """
        加载文件列表（分批加载）
        
        Args:
            files: 文件信息列表
            icons: 图标字典
            show_all_sizes: 是否显示所有大小
            show_mtime: 是否显示修改时间
        """
        logger.info(f"[SimpleVirtualFileList] load_files called with {len(files)} files")
        
        # 停止之前的加载
        self._stop_loading()
        
        # 清空列表（但不清空 _all_files，因为还没有设置）
        self._timer.stop()
        super().clear()
        self._loaded_count = 0
        logger.info(f"[SimpleVirtualFileList] list cleared, topLevelItemCount={self.topLevelItemCount()}")
        
        # 保存参数（在清空之后）
        self._all_files = files
        self._icons = icons
        self._show_all_sizes = show_all_sizes
        self._show_mtime = show_mtime
        self._is_loading = True
        logger.info(f"[load_files] _is_loading set to True, _all_files has {len(self._all_files)} files")
        
        # 开始分批加载
        if files:
            # 立即加载第一批
            logger.info(f"[SimpleVirtualFileList] starting batch load, batch_size={self._batch_size}")
            self._load_batch_sync()
        else:
            self._is_loading = False
            self.set_empty_hint(self._translation.get("empty_dir_hint", "当前目录为空"))
    
    def _load_batch_sync(self):
        """同步加载一批（立即执行）"""
        if not self._is_loading:
            logger.info("[SimpleVirtualFileList] _load_batch_sync: not loading, returning")
            return
        
        logger.info(f"[SimpleVirtualFileList] _load_batch_sync: loaded={self._loaded_count}, total={len(self._all_files)}")
        
        from utils.file_utils import get_file_type
        from utils.size_utils import format_size
        from utils.time_utils import format_mtime_timestamp
        
        # 计算当前批次
        start = self._loaded_count
        end = min(start + self._batch_size, len(self._all_files))
        batch = self._all_files[start:end]
        
        # 创建项
        for info in batch:
            name = info['name']
            path = info['path']
            is_dir = info.get('is_dir', False)
            
            # 大小列
            if is_dir:
                size = self._translation.get("folder", "<文件夹>")
                if self._show_all_sizes:
                    size = self._translation.get("calculating", "计算中")
            else:
                size = format_size(info.get('size', 0))
            
            # 修改时间列
            mtime = ""
            if self._show_mtime and info.get('mtime'):
                mtime = format_mtime_timestamp(info['mtime'])
            
            # 创建项
            item = QTreeWidgetItem([name, size, mtime])
            item.setData(0, Qt.ItemDataRole.UserRole, path)
            
            # 设置图标
            file_type = 'folder' if is_dir else get_file_type(name)
            icon = self._icons.get(file_type, self._icons.get('default'))
            if icon:
                item.setIcon(0, icon)
            
            # 隐藏文件灰色显示
            if self._is_hidden_file(path):
                item.setForeground(0, QColor(Qt.GlobalColor.gray))
            
            item.setToolTip(0, name)
            self.addTopLevelItem(item)
        
        self._loaded_count = end
        logger.info(f"[SimpleVirtualFileList] batch loaded: {start}-{end}, topLevelItemCount={self.topLevelItemCount()}")
        
        # 如果还有更多，延迟加载下一批
        if end < len(self._all_files):
            # 使用 QTimer 延迟加载，可以取消
            self._timer.start(10)
        else:
            self._is_loading = False
            # 清除空提示
            self.set_empty_hint("")
    
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
    
    def _stop_loading(self):
        """停止加载"""
        logger.info(f"[_stop_loading] called, current _is_loading={self._is_loading}")
        self._is_loading = False
        # 停止定时器，防止旧的加载任务继续执行
        self._timer.stop()
        logger.info(f"[_stop_loading] timer stopped")
    
    def clear(self):
        """清空列表"""
        # 只停止定时器，不修改 _is_loading 标志
        self._timer.stop()
        super().clear()
        self._all_files = []
        self._loaded_count = 0
    
    def filter_files(self, keyword: str) -> int:
        """过滤文件"""
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
    
    def set_empty_hint(self, text: str):
        """设置空提示"""
        # 如果列表为空且有提示文本，显示提示
        if text and self.topLevelItemCount() == 0:
            item = QTreeWidgetItem([text, "", ""])
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(0, QColor(Qt.GlobalColor.gray))
            self.addTopLevelItem(item)
    
    def get_selected_paths(self) -> List[str]:
        """获取选中的文件路径"""
        paths = []
        for item in self.selectedItems():
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path:
                paths.append(path)
        return paths
    
    def _on_item_activated(self, item: QTreeWidgetItem, column: int):
        """项被激活"""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path:
            self.file_activated.emit(path)


def create_simple_virtual_list(parent=None, batch_size: int = 100) -> SimpleVirtualFileList:
    """创建简化版虚拟列表"""
    return SimpleVirtualFileList(parent, batch_size)
