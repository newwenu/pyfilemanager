import os
import sys
from PySide6.QtWidgets import QTreeWidgetItem, QTreeWidget
from PySide6.QtCore import Qt, QFileSystemWatcher, QTimer
from PySide6.QtGui import QColor
from utils.file_utils import get_file_type
from utils.size_utils import format_size
from dbload_manager.file_tree_manager import FileTreeManager, CacheValidity
from threads.file_list_loader import FileListLoaderManager
from handlers.header_sort_handler import HeaderSortHandler
from core.sort_index_mapper import sort_file_list
from image_manager.ink_icon import get_shortcut_icon_pixmap
from utils.logging_config import get_logger, log_performance, log_exception, LogContext

# 导入事件总线和配置
from core import event_bus, app_config

logger = get_logger(__name__)


class FileListUpdater:
    """
    文件列表更新器 - 使用事件总线进行通信

    通过事件总线发送UI更新请求，而不是直接操作主窗口
    """

    def __init__(self, main_window):
        """
        初始化文件列表更新器

        Args:
            main_window: 主窗口实例（用于获取必要的状态和控件）
        """
        self._main_window = main_window
        self._translation = main_window.translation
        self.folder_threads = {}

        # 初始化异步加载管理器
        self.file_list_loader = FileListLoaderManager(main_window)
        self.file_list_loader.list_loaded.connect(self._update_filelist_from_thread)
        self.file_list_loader.error_occurred.connect(self._handle_scan_error)

        # 初始化排序处理器
        self.header_handler = HeaderSortHandler(self)

        # 缓存文件列表数据
        self.file_list_data = []
        self.show_mtime = app_config.show_mtime
        self.last_updated_path = None
        self.error_occurred = False

        # 文件夹大小计算防抖定时器（用于排序刷新）
        self._sort_refresh_timer = QTimer(self._main_window)
        self._sort_refresh_timer.setSingleShot(True)
        self._sort_refresh_timer.timeout.connect(self._refresh_sort_after_size_calc)
        self._pending_sort_refresh = False  # 标记是否有待执行的排序刷新

        # 初始化文件夹监控（低开销，只监控当前目录）
        # 使用 main_window 作为 parent（QFileSystemWatcher 需要 QObject parent）
        self._folder_watcher = QFileSystemWatcher(main_window)
        self._folder_watcher.directoryChanged.connect(self._on_folder_changed)
        self._watched_path = None

        # 连接事件总线
        self._setup_event_bus_connections()

    def _setup_event_bus_connections(self):
        """设置事件总线连接"""
        # 监听配置变更事件
        event_bus.config_changed.connect(self._on_config_changed)
        # 监听文件列表更新事件
        event_bus.ui_update_filelist.connect(self.update_filelist)

    def _on_config_changed(self, key: str, value):
        """处理配置变更事件"""
        if key == "show_mtime":
            self.show_mtime = value
        elif key in ("scan_exclude_system_protected", "scan_exclude_custom"):
            # 扫描排除配置变更，清除过滤器缓存并刷新文件列表
            from utils.file_filter import get_file_filter
            get_file_filter().clear_cache()
            self.update_filelist()

    # ========== 属性访问（保持向后兼容）==========

    @property
    def file_list(self) -> QTreeWidget:
        """获取文件列表控件"""
        return self._main_window.file_list

    @property
    def current_path(self) -> str:
        """获取当前路径"""
        return self._main_window.current_path

    @property
    def show_hidden(self) -> bool:
        """获取是否显示隐藏文件"""
        return self._main_window.show_hidden

    @property
    def show_all_sizes(self) -> bool:
        """获取是否显示所有大小"""
        return self._main_window.show_all_sizes

    @property
    def icons(self) -> dict:
        """获取图标集合"""
        return self._main_window.icons

    @property
    def file_tree_manager(self) -> FileTreeManager:
        """获取 FileTreeManager 实例"""
        return self._main_window.file_tree_manager

    @property
    def db(self):
        """获取数据库实例（向后兼容）"""
        return self._main_window.file_tree_manager

    @property
    def folder_size_manager(self):
        """获取文件夹大小管理器"""
        return self._main_window.folder_size_manager

    # ========== 核心功能 ==========

    @log_performance(logger, "更新文件列表")
    def update_filelist(self):
        """更新文件列表（核心功能）"""
        self._clean_old_threads()
        self.file_list.clear()
        self._setup_header_layout()

        # 切换文件夹监控到当前目录
        self._switch_folder_watcher(self.current_path)

        try:
            # 启动异步加载线程
            self.file_list_loader.start_load(self.current_path, self.show_hidden)
            self.last_updated_path = self.current_path
            self.error_occurred = False
        except Exception as e:
            log_exception(logger, "文件列表更新失败", e)
            # 使用事件总线发送错误消息
            event_bus.ui_update_statusbar.emit(f"文件列表更新失败: {str(e)}", 5000)

    def _switch_folder_watcher(self, path: str):
        """
        切换文件夹监控到指定路径

        只监控当前浏览的目录，开销极小（~10KB内存）
        """
        # 移除旧监控
        if self._watched_path and self._watched_path in self._folder_watcher.directories():
            self._folder_watcher.removePath(self._watched_path)
            logger.debug(f"停止监控: {self._watched_path}")

        # 添加新监控（只监控有效目录）
        if path and os.path.isdir(path) and path not in ['此电脑', '']:
            if self._folder_watcher.addPath(path):
                self._watched_path = path
                logger.debug(f"开始监控当前目录: {path}")
            else:
                logger.warning(f"无法监控目录（可能无权限）: {path}")
                self._watched_path = None
        else:
            self._watched_path = None

    def _on_folder_changed(self, path: str):
        """
        检测到当前目录变化时的回调

        触发文件列表刷新和文件夹大小重新计算
        """
        logger.info(f"检测到目录变化: {path}")

        # 标记相关缓存失效
        if self.file_tree_manager:
            self.file_tree_manager.invalidate_cache(path)

        # 发送状态栏提示
        event_bus.ui_update_statusbar.emit("检测到文件夹变化，正在刷新...", 3000)

        # 延迟刷新（避免频繁变化导致频繁刷新）
        from PySide6.QtCore import QTimer
        QTimer.singleShot(500, self._refresh_after_change)

    def _refresh_after_change(self):
        """变化后刷新文件列表"""
        if self._watched_path and os.path.exists(self._watched_path):
            logger.debug(f"刷新文件列表: {self._watched_path}")
            self.update_filelist()

    def _setup_header_layout(self):
        """设置文件列表列布局"""
        if self.current_path == '此电脑':
            return

        # 设置表头
        headers = [
            self._translation.get("name", "名称"),
            self._translation.get("size", "大小")
        ]

        if self.show_mtime:
            headers.append(self._translation.get("mtime", "修改时间"))

        self.file_list.setColumnHidden(2, not self.show_mtime)
        self.file_list.setHeaderLabels(headers)
        self.file_list.setColumnWidth(0, 400)
        self.file_list.setColumnWidth(1, 100)

        if self.show_mtime:
            self.file_list.setColumnWidth(2, 150)

    def _clean_old_threads(self):
        """清理未完成的文件夹大小计算线程"""
        for path, thread in list(self.folder_threads.items()):
            thread.stop()
            thread.wait()
            thread.deleteLater()
            del self.folder_threads[path]

    def start_folder_size_thread(self, path, item):
        """启动文件夹大小计算线程"""
        if path in self.folder_threads:
            return
        thread = self.folder_size_manager.start_calculate(path, item)
        if thread is not None:
            self.folder_threads[path] = thread

    def _apply_hidden_style2(self, item, entry):
        """应用隐藏文件灰色显示样式"""
        try:
            if sys.platform == "win32":
                import win32api
                import win32con
                is_hidden = win32api.GetFileAttributes(entry) & win32con.FILE_ATTRIBUTE_HIDDEN
            else:
                is_hidden = os.path.basename(entry).startswith('.')

            if is_hidden:
                item.setForeground(0, QColor(Qt.GlobalColor.gray))
        except Exception:
            pass

    def _handle_folder_size_calculation2(self, entry, item):
        """处理文件夹大小异步计算及缓存 - 使用 FileTreeManager"""
        folder_path = entry

        # 使用 FileTreeManager 获取文件夹信息（自动验证缓存有效性）
        folder_info = self.file_tree_manager.get_folder_info(folder_path)

        if folder_info.cache_status == CacheValidity.VALID:
            # 缓存有效，直接使用
            if folder_info.size == 0 and folder_info.formatted_size == "计算中...":
                # 特殊情况：缓存存在但大小为0，可能是新缓存
                self.start_folder_size_thread(folder_path, item)
            else:
                item.setText(1, folder_info.formatted_size)
                self._update_file_list_data(folder_path, folder_info.formatted_size, folder_info.size)

                # 如果虚拟列表有更新方法，调用它
                if hasattr(self.file_list, 'update_folder_size'):
                    self.file_list.update_folder_size(folder_path, folder_info.formatted_size)
        elif folder_info.cache_status == CacheValidity.NOT_CACHED:
            # 无缓存，启动计算线程
            self.start_folder_size_thread(folder_path, item)
        else:
            # 缓存失效（修改时间变化、内容变化或过期），重新计算
            self.start_folder_size_thread(folder_path, item)

    def _update_file_list_data(self, folder_path: str, display_size: str, size: int):
        """更新文件列表数据中的大小信息"""
        for info in self.file_list_data:
            if info["path"] == folder_path:
                info["display_size"] = display_size
                info["size"] = size
                break

    def _update_status_bar(self, file_count, folder_count):
        """更新状态栏信息"""
        if self.error_occurred:
            return

        total = file_count + folder_count

        # 使用标准的 selectedItems() 方法获取选中数量
        # 虚拟列表已经完全兼容此接口
        selected_count = len(self.file_list.selectedItems())

        status_template = self._translation.get(
            "status_text",
            "{current_path} | 总数：{total} | 文件：{file_count} | 文件夹：{folder_count} | 选中：{selected_count}"
        )
        status_text = status_template.format(
            current_path=self.current_path,
            total=total,
            file_count=file_count,
            folder_count=folder_count,
            selected_count=selected_count
        )
        # 使用事件总线更新状态栏
        event_bus.ui_update_statusbar.emit(status_text, 0)

    def filter_files(self, keyword: str):
        """根据关键词过滤文件列表项"""
        # 如果虚拟列表有自己的过滤方法，使用它
        if hasattr(self.file_list, 'filter_files') and callable(getattr(self.file_list, 'filter_files')):
            return self.file_list.filter_files(keyword)

        # 标准过滤方法
        match_count = 0
        for index in range(self.file_list.topLevelItemCount()):
            item = self.file_list.topLevelItem(index)
            file_name = item.text(0)
            if keyword in file_name:
                item.setHidden(False)
                match_count += 1
            else:
                item.setHidden(True)
        return match_count

    def clear_filter(self):
        """清除过滤，显示所有文件"""
        # 如果虚拟列表有自己的过滤方法，使用它
        if hasattr(self.file_list, 'filter_files') and callable(getattr(self.file_list, 'filter_files')):
            self.file_list.filter_files("")
            return

        # 标准清除方法
        for index in range(self.file_list.topLevelItemCount()):
            item = self.file_list.topLevelItem(index)
            item.setHidden(False)

    def _update_filelist_from_thread(self, file_list: list):
        """异步扫描完成后更新文件列表"""
        self.file_list_data = file_list

        # 应用当前排序状态
        from core.sort_state_manager import SortStateManager
        sort_manager = SortStateManager()
        current_state = sort_manager.state
        
        # 如果按大小排序，先尝试从缓存获取文件夹大小
        self._pending_sort_refresh = False
        if current_state.key == "size":
            uncached_folders = 0
            for info in file_list:
                if info.get("is_dir", False):
                    folder_info = self.file_tree_manager.get_folder_info(info["path"])
                    if folder_info.cache_status == CacheValidity.VALID:
                        info["size"] = folder_info.size
                        info["display_size"] = folder_info.formatted_size
                    else:
                        uncached_folders += 1
            
            # 如果有无缓存的文件夹，标记需要刷新（不显示开始提示，避免与完成提示重叠）
            if uncached_folders > 0:
                self._pending_sort_refresh = True
                logger.debug(f"按大小排序，{uncached_folders} 个文件夹大小待计算，将在完成后自动刷新排序")
        
        sorted_file_list = sort_file_list(
            file_list, 
            sort_key=current_state.key, 
            reverse=current_state.reverse,
            folders_grouped=current_state.folders_grouped,
            folders_before=current_state.folders_before
        )
        
        # 更新表头显示以反映当前排序状态
        self.header_handler._update_header_text(current_state)

        self.file_list.clear()
        file_count = folder_count = 0

        for info in sorted_file_list:
            if info["is_dir"]:
                folder_count += 1
            else:
                file_count += 1

            item = self._create_list_item_from_info(info)
            self._apply_hidden_style2(item, info["path"])

            if info["is_dir"] and self.show_all_sizes:
                self._handle_folder_size_calculation2(info["path"], item)

        self._update_status_bar(file_count, folder_count)

        # 设置空提示
        if file_count == 0 and folder_count == 0 and not self.error_occurred:
            self.file_list.set_empty_hint(self._translation.get("empty_dir_hint", "当前目录为空"))
        elif self.error_occurred:
            self.file_list.set_empty_hint(self._translation.get("error_hint", "发生错误或无权限访问"))
        else:
            self.file_list.set_empty_hint("")

    def trigger_sort_refresh(self):
        """触发排序刷新（供文件夹大小计算完成后调用，带防抖）"""
        if not self._pending_sort_refresh:
            return
        
        # 重置定时器（防抖：500ms内多次调用只执行最后一次）
        self._sort_refresh_timer.stop()
        self._sort_refresh_timer.start(500)
    
    def _refresh_sort_after_size_calc(self):
        """文件夹大小计算完成后刷新排序"""
        if not self._pending_sort_refresh:
            return
        
        # 检查是否还有正在计算的文件夹
        active_threads = getattr(self._main_window.folder_size_manager, 'threads', {})
        if active_threads:
            # 还有计算中的文件夹，继续等待
            self._sort_refresh_timer.start(500)
            return
        
        # 所有文件夹大小计算完成，执行重新排序
        self._pending_sort_refresh = False
        
        # 获取当前排序状态
        from core.sort_state_manager import SortStateManager
        sort_manager = SortStateManager()
        current_state = sort_manager.state
        
        # 重新排序
        sorted_list = sort_file_list(
            self.file_list_data,
            sort_key=current_state.key,
            reverse=current_state.reverse,
            folders_grouped=current_state.folders_grouped,
            folders_before=current_state.folders_before
        )
        
        # 更新UI
        self._update_filelist_from_sorted(sorted_list)
        
        # 显示完成提示（通过事件总线，使用tip_id便于管理）
        event_bus.ui_show_message.emit("success", "文件夹大小计算完成，排序已刷新", "sort_refresh_complete")
        logger.debug("文件夹大小计算完成，自动刷新排序")

    def _update_filelist_from_sorted(self, filelist2: list):
        """从排序后的文件列表更新UI"""
        if not filelist2:
            return
        
        # 更新缓存的数据为排序后的顺序
        self.file_list_data = filelist2
        
        # 批量操作优化：禁用UI更新和重绘，减少闪烁
        self.file_list.setUpdatesEnabled(False)
        
        try:
            self.file_list.clear()
            for info in filelist2:
                item = self._create_list_item_from_info(info)
                self._apply_hidden_style2(item, info["path"])
                if info["is_dir"] and self.show_all_sizes:
                    self._handle_folder_size_calculation2(info["path"], item)
                self.file_list.addTopLevelItem(item)
        finally:
            # 恢复UI更新
            self.file_list.setUpdatesEnabled(True)
            self.file_list.viewport().update()

    def _create_list_item_from_info(self, info: dict):
        """创建列表项"""
        file_type = 'folder' if info["is_dir"] else get_file_type(info["name"])

        if info["is_dir"]:
            if self.show_all_sizes:
                size = info.get("display_size", self._translation.get("calculating", "计算中"))
            else:
                size = self._translation.get("folder", "<文件夹>")
        else:
            size = format_size(info.get("display_size", info["size"]))

        item = QTreeWidgetItem(self.file_list, [info["name"], size])
        item.setData(0, Qt.ItemDataRole.UserRole, info["path"])

        file_path = info["path"]

        # 检查是否使用系统图标（按扩展名或default类型）
        from image_manager.icon_settings_manager import get_icon_settings_manager
        icon_settings = get_icon_settings_manager()
        file_ext = os.path.splitext(info["name"])[1].lower()
        use_system_icon_by_ext = icon_settings.is_use_system_icon(file_ext)
        use_system_icon_by_default = (file_type == 'default' and icon_settings.is_use_system_icon_for_default())
        use_system_icon = use_system_icon_by_ext or use_system_icon_by_default

        # 特殊处理快捷方式文件或使用系统图标的扩展名/default类型
        if file_type == 'shortcut' or (use_system_icon and not info["is_dir"]):
            from PySide6.QtGui import QIcon
            icon_size = app_config.file_list_icon_size
            pixmap = get_shortcut_icon_pixmap(file_path, icon_size)

            if pixmap and not pixmap.isNull():
                item.setIcon(0, QIcon(pixmap))
            else:
                item.setIcon(0, self.icons.get(file_type, self.icons['default']))
        else:
            item.setIcon(0, self.icons.get(file_type, self.icons['default']))

        item.setToolTip(0, info["name"])

        if self.show_mtime:
            from utils.time_utils import format_mtime_timestamp
            if info["mtime"]:
                mtime_str = format_mtime_timestamp(info["mtime"])
                item.setText(2, mtime_str)

        return item

    def _handle_scan_error(self, error_msg):
        """处理扫描错误"""
        error_text = self._translation.get("scan_error", "当前目录扫描错误：{error_msg}").format(error_msg=error_msg)
        # 使用事件总线发送错误消息
        event_bus.ui_update_statusbar.emit(error_text, 5000)
        self.error_occurred = True
