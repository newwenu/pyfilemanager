from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QRadioButton, QPushButton, 
    QHBoxLayout, QCheckBox, QMenu
)
from PySide6.QtCore import Qt, QTimer

from core.sort_index_mapper import sort_file_list
from core.sort_state_manager import SortStateManager, SortState


class HeaderSortHandler:
    """
    表头排序处理器 - 优化防抖版
    
    优化点：
    1. 立即执行排序，不给用户延迟感
    2. 智能防抖：快速连续点击时只执行最后一次
    3. 排序过程中禁用表头点击，避免冲突
    4. 右键菜单弹出排序选项
    """
    
    def __init__(self, file_list_updater):
        self.fm = file_list_updater
        self._main_window = file_list_updater._main_window
        
        # 列索引与排序键的映射
        self.column_to_key = {
            0: "name",
            1: "size", 
            2: "mtime"
        }
        self.key_to_column = {v: k for k, v in self.column_to_key.items()}
        
        # 获取排序状态管理器（单例）
        self._sort_manager = SortStateManager()
        self._sort_manager.state_changed.connect(self._on_sort_state_changed)
        
        # 绑定表头事件
        self.file_list_header = self.fm.file_list.header()
        self.file_list_header.sectionClicked.connect(self.on_header_clicked)
        
        # 右键菜单 - 确保表头启用上下文菜单
        self.file_list_header.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list_header.customContextMenuRequested.connect(self.on_header_context_menu)
        # 确保表头可交互
        self.file_list_header.setSectionsClickable(True)
        
        # 防抖定时器 - 用于快速连续点击时只执行最后一次
        self._debounce_timer = QTimer(self._main_window)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._execute_sort)
        
        # 待执行的排序请求
        self._pending_request = None
        
        # 是否正在排序中
        self._is_sorting = False
        
        # 缓存原始表头标题
        self._original_headers = []
        self._cache_headers()
    
    def _cache_headers(self):
        """缓存原始表头标题"""
        count = self.file_list_header.count()
        self._original_headers = [
            self.file_list_header.model().headerData(i, Qt.Horizontal) or f"列{i}"
            for i in range(count)
        ]
    
    def on_header_clicked(self, logical_index):
        """
        单击表头 - 切换排序
        
        如果点击的是当前排序列，切换排序方向
        如果点击的是其他列，切换到该列并使用升序
        """
        if logical_index not in self.column_to_key:
            return
        
        # 如果正在排序，忽略点击（避免冲突）
        if self._is_sorting:
            return
        
        key = self.column_to_key[logical_index]
        
        # 保存排序请求
        self._pending_request = {
            'column': logical_index,
            'key': key
        }
        
        # 停止之前的防抖定时器
        self._debounce_timer.stop()
        
        # 立即执行排序（不给用户延迟感）
        self._execute_sort()
    
    def _execute_sort(self):
        """执行排序（立即执行）"""
        if self._pending_request is None:
            return
        
        # 标记正在排序
        self._is_sorting = True
        
        try:
            column = self._pending_request['column']
            key = self._pending_request['key']
            
            # 更新排序状态（这会触发 state_changed 信号）
            self._sort_manager.set_sort_column(column, key)
            
        finally:
            self._is_sorting = False
            self._pending_request = None
    
    def _on_sort_state_changed(self, state: SortState):
        """
        排序状态变化回调 - 立即执行排序
        
        注意：这里不做防抖，因为状态变化应该立即反映到UI
        """
        # 立即更新表头显示
        self._update_header_text(state)
        
        # 立即执行排序（不延迟）
        try:
            current_file_list = self.fm.file_list_data
            if not current_file_list:
                return
            
            sorted_list = sort_file_list(
                current_file_list,
                sort_key=state.key,
                reverse=state.reverse,
                folders_grouped=state.folders_grouped,
                folders_before=state.folders_before
            )
            
            # 更新UI
            self.fm._update_filelist_from_sorted(sorted_list)
            
        except Exception as e:
            from handlers.m_event_handlers import show_error
            show_error(self._main_window, "排序失败", str(e))
    
    def on_header_context_menu(self, position):
        """右键表头 - 显示排序选项菜单"""
        # 获取点击的列索引
        logical_index = self.file_list_header.logicalIndexAt(position)
        if logical_index not in self.column_to_key:
            return
        
        # 创建右键菜单
        menu = QMenu(self._main_window)
        menu.setWindowTitle("排序选项")
        
        current_state = self._sort_manager.state
        
        # 添加排序方式选项
        action_name = menu.addAction("按名称排序")
        action_name.setCheckable(True)
        action_name.setChecked(current_state.key == "name")
        action_name.triggered.connect(lambda: self._set_sort_key("name", 0))
        
        action_size = menu.addAction("按大小排序")
        action_size.setCheckable(True)
        action_size.setChecked(current_state.key == "size")
        action_size.triggered.connect(lambda: self._set_sort_key("size", 1))
        
        action_mtime = menu.addAction("按修改时间排序")
        action_mtime.setCheckable(True)
        action_mtime.setChecked(current_state.key == "mtime")
        action_mtime.triggered.connect(lambda: self._set_sort_key("mtime", 2))
        
        menu.addSeparator()
        
        # 添加排序方向选项
        action_asc = menu.addAction("升序 ↑")
        action_asc.setCheckable(True)
        action_asc.setChecked(not current_state.reverse)
        action_asc.triggered.connect(lambda: self._set_sort_order(False))
        
        action_desc = menu.addAction("降序 ↓")
        action_desc.setCheckable(True)
        action_desc.setChecked(current_state.reverse)
        action_desc.triggered.connect(lambda: self._set_sort_order(True))
        
        menu.addSeparator()
        
        # 添加文件夹归并选项
        action_folders_grouped = menu.addAction("文件夹归并")
        action_folders_grouped.setCheckable(True)
        action_folders_grouped.setChecked(current_state.folders_grouped)
        action_folders_grouped.triggered.connect(self._toggle_folders_grouped)
        
        # 添加文件夹在前选项
        action_folders_before = menu.addAction("文件夹在前")
        action_folders_before.setCheckable(True)
        action_folders_before.setChecked(current_state.folders_before)
        action_folders_before.triggered.connect(self._toggle_folders_before)
        
        # 显示菜单
        menu.exec(self.file_list_header.mapToGlobal(position))
    
    def _set_sort_key(self, key, column):
        """设置排序键"""
        new_state = SortState(
            column=column,
            key=key,
            reverse=self._sort_manager.state.reverse,
            folders_grouped=self._sort_manager.state.folders_grouped,
            folders_before=self._sort_manager.state.folders_before
        )
        self._sort_manager._set_state(new_state)
    
    def _set_sort_order(self, reverse):
        """设置排序方向"""
        self._sort_manager.set_sort_order(reverse)
    
    def _toggle_folders_grouped(self):
        """切换文件夹归并"""
        self._sort_manager.toggle_folders_grouped()
    
    def _toggle_folders_before(self):
        """切换文件夹在前"""
        self._sort_manager.toggle_folders_before()
    
    def _update_header_text(self, state: SortState):
        """更新表头文本显示排序状态"""
        # 重置所有表头为原始标题
        for i, title in enumerate(self._original_headers):
            self.fm.file_list.headerItem().setText(i, title)
        
        # 添加排序方向指示器
        direction = "↓" if state.reverse else "↑"
        if state.column < len(self._original_headers):
            title = self._original_headers[state.column]
            self.fm.file_list.headerItem().setText(
                state.column, 
                f"{title}{direction}"
            )
    
    def reset(self):
        """重置排序状态"""
        self._sort_manager.reset()
        self._cache_headers()
    
    def get_current_state(self):
        """获取当前排序状态"""
        return self._sort_manager.state
    
    def undo_sort(self):
        """撤销上一次排序"""
        if self._sort_manager.can_undo():
            self._sort_manager.undo()
