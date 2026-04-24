"""
虚拟文件列表组件 - 完全兼容版

解决大目录加载性能问题：
- 只渲染可见区域的项
- 支持数万文件不卡顿
- 平滑滚动体验
- 完全兼容 QTreeWidget 的所有接口

关键设计：
- 维护完整的数据模型
- 重写所有访问方法，让它们操作模型
- 只在渲染时使用虚拟滚动
- 对外完全透明，无需任何兼容代码
"""
from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QHeaderView,
    QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint
from PySide6.QtGui import QColor, QIcon
from typing import List, Dict, Optional, Set
import os
import logging

logger = logging.getLogger(__name__)


class VirtualFileListModel:
    """虚拟文件列表数据模型"""

    def __init__(self):
        self._all_files: List[Dict] = []
        self._filtered_files: List[Dict] = []
        self._sort_key = "name"
        self._sort_reverse = False

    def set_files(self, files: List[Dict]):
        """设置文件列表"""
        self._all_files = files
        self._apply_filter_and_sort()

    def filter(self, keyword: str):
        """过滤文件"""
        if not keyword:
            self._filtered_files = self._all_files.copy()
        else:
            keyword = keyword.lower()
            self._filtered_files = [
                f for f in self._all_files
                if keyword in f['name'].lower()
            ]
        self._apply_sort()

    def sort(self, key: str, reverse: bool = False):
        """排序文件"""
        self._sort_key = key
        self._sort_reverse = reverse
        self._apply_sort()

    def _apply_filter_and_sort(self):
        """应用过滤和排序"""
        self._filtered_files = self._all_files.copy()
        self._apply_sort()

    def _apply_sort(self):
        """应用排序"""
        from utils.sort_utils import sort_file_list
        self._filtered_files = sort_file_list(
            self._filtered_files,
            sort_key=self._sort_key,
            reverse=self._sort_reverse
        )

    def get_range(self, start: int, count: int) -> List[Dict]:
        """获取指定范围的文件"""
        end = min(start + count, len(self._filtered_files))
        return self._filtered_files[start:end]

    def get_file_at(self, index: int) -> Optional[Dict]:
        """获取指定索引的文件"""
        if 0 <= index < len(self._filtered_files):
            return self._filtered_files[index]
        return None

    def get_file_index(self, path: str) -> int:
        """获取文件索引"""
        for i, f in enumerate(self._filtered_files):
            if f['path'] == path:
                return i
        return -1

    def get_file_info(self, path: str) -> Optional[Dict]:
        """获取文件信息"""
        for f in self._filtered_files:
            if f['path'] == path:
                return f
        return None

    def update_file_info(self, path: str, **kwargs):
        """更新文件信息"""
        for f in self._filtered_files:
            if f['path'] == path:
                f.update(kwargs)
                return True
        return False

    @property
    def total_count(self) -> int:
        return len(self._filtered_files)

    @property
    def all_files(self) -> List[Dict]:
        return self._filtered_files.copy()


class VirtualFileList(QTreeWidget):
    """
    虚拟文件列表控件 - 完全兼容 QTreeWidget 接口

    特性：
    - 只渲染可见区域的项（高性能）
    - 完全兼容 QTreeWidget 的所有接口（透明替换）
    - 支持平滑滚动
    - 内存占用低（无论多少文件）
    """

    file_activated = Signal(str)  # 文件被激活
    selection_changed = Signal(list)  # 选中项变化
    visible_range_changed = Signal(int, int)  # 可见范围变化 (start, end)

    def __init__(self, parent=None, item_height: int = 28):
        super().__init__(parent)

        # 数据模型 - 存储所有文件
        self._model = VirtualFileListModel()

        # 配置
        self._item_height = item_height
        self._viewport_margin = 5  # 上下缓冲行数

        # 渲染状态
        self._visible_start = 0
        self._visible_end = 0
        self._icons: Dict[str, any] = {}
        self._show_all_sizes = False
        self._show_mtime = False
        self._is_updating = False

        # 选中状态 - 维护完整的选中集合
        self._selected_paths: Set[str] = set()
        self._current_path: Optional[str] = None

        # 设置UI
        self._setup_ui()

        # 滚动监听
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)

        # 延迟更新定时器
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._update_visible_items)

        # 选中变化
        self.itemSelectionChanged.connect(self._on_selection_changed)
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

        # 虚拟滚动优化设置
        self.setUniformRowHeights(True)  # 关键：统一行高
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setSelectionMode(QTreeWidget.ExtendedSelection)

        # 显示滚动条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

    # ==================== 兼容接口：列设置 ====================

    def setup_columns(self, show_mtime: bool = False):
        """设置列（兼容接口）"""
        self.setColumnCount(3 if show_mtime else 2)

    def set_empty_hint(self, text: str):
        """设置空提示（兼容接口）"""
        # 如果列表为空且有提示文本，显示提示
        if text and self._model.total_count == 0:
            item = QTreeWidgetItem([text, "", ""])
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(0, QColor(Qt.GlobalColor.gray))
            self.addTopLevelItem(item)

    # ==================== 核心：文件加载 ====================

    def load_files(self, files: List[Dict], icons: Dict,
                   show_all_sizes: bool = False, show_mtime: bool = False):
        """加载文件列表"""
        logger.info(f"[VirtualFileList] load_files called with {len(files)} files")

        self._is_updating = True

        # 保存参数
        self._icons = icons
        self._show_all_sizes = show_all_sizes
        self._show_mtime = show_mtime

        # 保留选中状态（如果文件仍然存在）
        old_selected = self._selected_paths.copy()
        old_current = self._current_path

        # 设置数据
        self._model.set_files(files)
        logger.info(f"[VirtualFileList] model has {self._model.total_count} files")

        # 验证并恢复选中状态
        self._selected_paths = {p for p in old_selected if self._model.get_file_index(p) >= 0}
        if old_current and self._model.get_file_index(old_current) >= 0:
            self._current_path = old_current
        else:
            self._current_path = None

        # 更新滚动条
        self._update_scrollbar()

        # 重置滚动位置
        self.verticalScrollBar().setValue(0)

        self._is_updating = False

        # 更新可见项
        self._update_visible_items()

    def _update_scrollbar(self):
        """更新滚动条范围"""
        total_height = self._model.total_count * self._item_height
        viewport_height = self.viewport().height()

        # 设置滚动条范围
        max_value = max(0, total_height - viewport_height)
        self.verticalScrollBar().setRange(0, max_value)
        self.verticalScrollBar().setSingleStep(self._item_height)
        self.verticalScrollBar().setPageStep(viewport_height)

    # ==================== 核心：虚拟滚动渲染 ====================

    def _on_scroll(self, value: int):
        """滚动事件"""
        if self._is_updating:
            return

        # 延迟更新，避免频繁刷新
        self._update_timer.stop()
        self._update_timer.start(30)  # 30ms 延迟

    def _update_visible_items(self):
        """更新可见项"""
        if self._is_updating:
            return

        # 计算可见范围
        scroll_value = self.verticalScrollBar().value()
        viewport_height = self.viewport().height()

        # 如果视口高度为0（尚未显示），使用一个默认值
        if viewport_height == 0:
            viewport_height = 600

        # 计算可见的起始和结束索引
        start_idx = max(0, scroll_value // self._item_height - self._viewport_margin)
        end_idx = min(
            self._model.total_count,
            (scroll_value + viewport_height) // self._item_height + self._viewport_margin
        )

        # 确保至少渲染一些项
        if end_idx <= start_idx:
            end_idx = min(start_idx + 20, self._model.total_count)

        # 如果范围没有变化，不更新
        if (start_idx, end_idx) == (self._visible_start, self._visible_end):
            return

        self._visible_start = start_idx
        self._visible_end = end_idx

        # 发送可见范围变化信号
        self.visible_range_changed.emit(start_idx, end_idx)

        # 重新渲染
        self._render_items(start_idx, end_idx)

    def _render_items(self, start: int, end: int):
        """渲染指定范围的项"""
        from utils.file_utils import get_file_type
        from utils.size_utils import format_size
        from utils.time_utils import format_mtime_timestamp
        from image_manager.ink_icon import get_shortcut_icon_pixmap
        from core import app_config

        logger.debug(f"[VirtualFileList] _render_items: {start}-{end}")

        # 清空并重新创建项
        super().clear()

        # 获取可见范围的文件
        files = self._model.get_range(start, end - start)

        for i, info in enumerate(files):
            name = info['name']
            path = info['path']
            is_dir = info.get('is_dir', False)

            # 创建项
            item = self._create_item_from_info(info)
            self.addTopLevelItem(item)

            # 恢复选中状态
            if path in self._selected_paths:
                item.setSelected(True)

            # 恢复当前项
            if path == self._current_path:
                self.setCurrentItem(item)

        # 设置视口边距，模拟完整列表高度
        top_margin = start * self._item_height
        bottom_margin = (self._model.total_count - end) * self._item_height
        self.setViewportMargins(0, top_margin, 0, bottom_margin)

    def _create_item_from_info(self, info: Dict) -> QTreeWidgetItem:
        """从文件信息创建 QTreeWidgetItem"""
        from utils.file_utils import get_file_type
        from utils.size_utils import format_size
        from utils.time_utils import format_mtime_timestamp
        from image_manager.ink_icon import get_shortcut_icon_pixmap
        from core import app_config

        name = info['name']
        path = info['path']
        is_dir = info.get('is_dir', False)

        # 大小列
        if is_dir:
            size = info.get("display_size", "<文件夹>" if not self._show_all_sizes else "计算中")
        else:
            size = info.get("display_size", format_size(info.get('size', 0)))

        # 修改时间列
        mtime = ""
        if self._show_mtime and info.get('mtime'):
            mtime = format_mtime_timestamp(info['mtime'])

        # 创建项
        item = QTreeWidgetItem([name, size, mtime])
        item.setData(0, Qt.ItemDataRole.UserRole, path)

        # 设置图标
        file_type = 'folder' if is_dir else get_file_type(name)

        # 特殊处理快捷方式
        if file_type == 'shortcut' or (file_type == 'defaulticon' and not is_dir):
            try:
                icon_size = app_config.file_list_icon_size
                pixmap = get_shortcut_icon_pixmap(path, icon_size)
                if pixmap and not pixmap.isNull():
                    item.setIcon(0, QIcon(pixmap))
                else:
                    icon = self._icons.get(file_type, self._icons.get('default'))
                    if icon:
                        item.setIcon(0, icon)
            except Exception as e:
                logger.warning(f"获取快捷方式图标失败: {path}, {e}")
                icon = self._icons.get(file_type, self._icons.get('default'))
                if icon:
                    item.setIcon(0, icon)
        else:
            icon = self._icons.get(file_type, self._icons.get('default'))
            if icon:
                item.setIcon(0, icon)

        # 隐藏文件灰色显示
        if info.get('is_hidden'):
            item.setForeground(0, QColor(Qt.GlobalColor.gray))

        item.setToolTip(0, name)

        return item

    # ==================== 关键：完全兼容 QTreeWidget 的接口 ====================

    def topLevelItemCount(self) -> int:
        """
        获取顶层项数量 - 关键兼容方法
        返回模型中的总数，而不是可见数量
        """
        return self._model.total_count

    def topLevelItem(self, index: int) -> Optional[QTreeWidgetItem]:
        """
        获取指定索引的顶层项 - 关键兼容方法
        从模型创建虚拟项，而不是从可见项
        """
        if 0 <= index < self._model.total_count:
            info = self._model.get_file_at(index)
            if info:
                return self._create_item_from_info(info)
        return None

    def indexOfTopLevelItem(self, item: QTreeWidgetItem) -> int:
        """
        获取项的索引 - 关键兼容方法
        """
        if not item:
            return -1
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path:
            return self._model.get_file_index(path)
        return -1

    def selectedItems(self) -> List[QTreeWidgetItem]:
        """
        获取所有选中的项 - 关键兼容方法
        返回所有选中的项（包括不可见的），而不是仅可见的
        """
        items = []
        for path in self._selected_paths:
            info = self._model.get_file_info(path)
            if info:
                items.append(self._create_item_from_info(info))
        return items

    def currentItem(self) -> Optional[QTreeWidgetItem]:
        """
        获取当前项 - 关键兼容方法
        从模型获取，而不是从可见项
        """
        if self._current_path:
            info = self._model.get_file_info(self._current_path)
            if info:
                return self._create_item_from_info(info)
        # 如果没有记录的当前项，尝试从父类获取
        item = super().currentItem()
        if item:
            return item
        return None

    def setCurrentItem(self, item: QTreeWidgetItem):
        """设置当前项"""
        if item:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            self._current_path = path
            # 确保该项在可见区域
            index = self._model.get_file_index(path)
            if index >= 0:
                self._ensure_visible(index)
        super().setCurrentItem(item)

    def itemAt(self, pos: QPoint) -> Optional[QTreeWidgetItem]:
        """
        获取指定位置的项 - 关键兼容方法
        """
        # 先尝试标准方法
        item = super().itemAt(pos)
        if item:
            return item

        # 如果没有找到，计算位置对应的索引
        index = self._pos_to_index(pos)
        if 0 <= index < self._model.total_count:
            info = self._model.get_file_at(index)
            if info:
                return self._create_item_from_info(info)
        return None

    def _pos_to_index(self, pos: QPoint) -> int:
        """将位置转换为索引"""
        scroll_value = self.verticalScrollBar().value()
        y = pos.y() + scroll_value - self.viewportMargins().top()
        index = y // self._item_height
        return index

    def _ensure_visible(self, index: int):
        """确保指定索引的项在可见区域"""
        if self._visible_start <= index < self._visible_end:
            return  # 已经在可见区域

        # 滚动到该项
        scroll_value = index * self._item_height
        self.verticalScrollBar().setValue(scroll_value)

    def clear(self):
        """清空列表"""
        super().clear()
        self._visible_start = 0
        self._visible_end = 0
        self.setViewportMargins(0, 0, 0, 0)
        self._selected_paths.clear()
        self._current_path = None
        self._model = VirtualFileListModel()

    # ==================== 选中状态管理 ====================

    def _on_selection_changed(self):
        """选中项变化 - 维护完整的选中路径集合"""
        # 获取当前可见的选中项
        visible_selected = set()
        for item in super().selectedItems():
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path:
                visible_selected.add(path)

        # 更新选中路径集合
        self._selected_paths = visible_selected

        # 更新当前项
        current = super().currentItem()
        if current:
            self._current_path = current.data(0, Qt.ItemDataRole.UserRole)

        # 发送信号
        self.selection_changed.emit(list(self._selected_paths))

    def _on_item_activated(self, item: QTreeWidgetItem, column: int):
        """项被激活"""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path:
            self.file_activated.emit(path)

    # ==================== 其他功能方法 ====================

    def scroll_to_file(self, path: str):
        """滚动到指定文件"""
        index = self._model.get_file_index(path)
        if index >= 0:
            scroll_value = index * self._item_height
            self.verticalScrollBar().setValue(scroll_value)
            self._current_path = path
            self._update_visible_items()

    def filter_files(self, keyword: str) -> int:
        """过滤文件"""
        self._model.filter(keyword)
        self._update_scrollbar()
        self.verticalScrollBar().setValue(0)
        self._update_visible_items()
        return self._model.total_count

    def sort_files(self, key: str, reverse: bool = False):
        """排序文件"""
        self._model.sort(key, reverse)
        self._update_visible_items()

    def update_folder_size(self, path: str, size: str):
        """更新文件夹大小"""
        # 更新模型中的数据
        if self._model.update_file_info(path, display_size=size):
            # 如果当前可见，更新显示
            for i in range(super().topLevelItemCount()):
                item = super().topLevelItem(i)
                if item and item.data(0, Qt.ItemDataRole.UserRole) == path:
                    item.setText(1, size)
                    break

    def get_selected_paths(self) -> List[str]:
        """获取选中的文件路径"""
        return list(self._selected_paths)

    def select_file(self, path: str, add_to_selection: bool = False):
        """选中指定文件"""
        if not add_to_selection:
            self._selected_paths.clear()

        if path:
            self._selected_paths.add(path)
            self._current_path = path

        self.scroll_to_file(path)

    # ==================== 事件处理 ====================

    def resizeEvent(self, event):
        """窗口大小变化"""
        super().resizeEvent(event)
        self._update_scrollbar()
        self._update_visible_items()

    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown,
                          Qt.Key_Home, Qt.Key_End):
            # 先执行默认行为
            super().keyPressEvent(event)
            # 更新当前项
            current = super().currentItem()
            if current:
                path = current.data(0, Qt.ItemDataRole.UserRole)
                self._current_path = path
                # 确保选中当前项
                if event.key() in (Qt.Key_Up, Qt.Key_Down):
                    if self.selectionMode() == QAbstractItemView.SingleSelection:
                        self._selected_paths = {path}
                    else:
                        self._selected_paths.add(path)
        else:
            super().keyPressEvent(event)
