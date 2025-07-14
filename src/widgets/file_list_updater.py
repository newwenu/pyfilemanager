import os
import sys
from PySide6.QtWidgets import QTreeWidgetItem, QTreeWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from utils.file_utils import get_file_type, format_size
from dbload_manager.database_manager import DatabaseManager
from threads.file_list_loader import FileListLoaderManager  # 导入
from handlers.header_sort_handler import HeaderSortHandler  # 新增导入
from utils.sort_utils import sort_file_list  # 新增：导入排序工具
from utils.logging_config import get_logger
import weakref  # 新增弱引用模块导入
logger = get_logger(__name__)
class FileListUpdater:
    def __init__(self, fm):  # 仅传递主窗口实例
        self.fm = fm  # 持有主窗口引用
        # 新增：获取翻译字典（假设主窗口已加载翻译）
        self.translation = self.fm.translation
        self.folder_threads = {}  # 实例变量：在FileListUpdater内部维护线程字典
        # ：初始化异步加载管理器
        self.file_list_loader = FileListLoaderManager(self.fm)
        self.file_list_loader.list_loaded.connect(self._update_filelist_from_thread)
        self.file_list_loader.error_occurred.connect(self._handle_scan_error)  # 新增错误处理
        # 可选：连接进度信号（用于显示加载提示）
        # self.file_list_loader.progress_updated.connect(self._update_progress)
        # 新增：初始化排序处理器并连接表头事件
        self.header_handler = HeaderSortHandler(self)
        # 新增：缓存文件列表数据（用于排序）
        self.file_list_data = []  
        self.show_mtime = self.fm.config_manager.config.get("show_mtime", False)
        self.last_updated_path = None  # 新增：记录最后一次更新的路径
        self.error_occurred = False
        # 新增：绑定文件夹展开事件
        self.file_list.itemExpanded.connect(self.on_folder_expanded)
        # 新增：记录已加载子目录的路径（避免重复加载）
        self.loaded_subdirs = set()
        
    @property
    def file_list(self) -> QTreeWidget:
        """通过主窗口直接获取文件列表控件"""
        return self.fm.file_list

    @property
    def current_path(self) -> str:
        """通过主窗口直接获取当前路径"""
        return self.fm.current_path

    @property
    def show_hidden(self) -> bool:
        """通过主窗口直接获取是否显示隐藏文件"""
        return self.fm.show_hidden

    @property
    def show_all_sizes(self) -> bool:
        """通过主窗口直接获取是否显示所有大小"""
        return self.fm.show_all_sizes

    @property
    def icons(self) -> dict:
        """通过主窗口直接获取图标集合"""
        return self.fm.icons

    @property
    def db(self) -> DatabaseManager:
        """通过主窗口直接获取数据库实例"""
        return self.fm.db

    @property
    def folder_size_manager(self):
        """通过主窗口直接获取文件夹大小管理器"""
        return self.fm.folder_size_manager

    # 删除原folder_threads属性（关键修改）
    # @property
    # def folder_threads(self) -> dict:
    #     """通过主窗口直接获取线程存储字典"""
    #     return self.fm.folder_threads

    def update_filelist(self):
        """更新文件列表（核心功能）"""
        # self.file_list_loader.stop_all()  # 触发管理器清理
        self._clean_old_threads()
        self.file_list.clear()
        self._setup_header_layout()  # 设置列布局
        # 可选：显示加载中的提示（如“加载中...”）

        try:
            # file_count, folder_count = self._process_directory_entries()  # 处理目录条目
            # self._update_status_bar(file_count, folder_count)  # 更新状态栏
            # ：启动异步加载线程
            self.file_list_loader.start_load(self.current_path, self.show_hidden)
            self.last_updated_path = self.current_path
            self.error_occurred = False
        except Exception as e:
            # 错误提示
            # print(f"文件列表更新失败: {str(e)}")
            logger.error(f"文件列表更新失败: {str(e)}")
            self.fm.status_bar.showMessage(f"文件列表更新失败: {str(e)}", 5000)

    def _setup_header_layout(self):
        """设置文件列表列布局（修改：使用翻译文本）"""
        if not self.current_path == '此电脑':
            # 从翻译获取表头文本（默认值为原硬编码）
            headers = [
                self.translation.get("file_list_name", "名称"),  # 名称列翻译
                self.translation.get("file_list_size", "大小")   # 大小列翻译
            ]
            # 根据配置添加时间列（使用翻译）
            show_mtime = self.show_mtime
            if show_mtime:
                headers.append(self.translation.get("file_list_mtime", "修改时间"))  # 修改时间列翻译
            self.file_list.setColumnHidden(2, not show_mtime)  # 隐藏条件不变
            
            self.file_list.setHeaderLabels(headers)
            self.file_list.setColumnWidth(0, 400)
            self.file_list.setColumnWidth(1, 100)
            if self.show_mtime:
                self.file_list.setColumnWidth(2, 150)

    def _clean_old_threads(self):
        """清理未完成的文件夹大小计算线程（操作内部字典）"""
        for path, thread in list(self.folder_threads.items()):
            thread.stop()
            thread.wait()
            thread.deleteLater()
            del self.folder_threads[path]

    def start_folder_size_thread(self, path, item):
        """启动文件夹大小计算线程（使用内部字典存储）"""
        if path in self.folder_threads:  # 避免重复启动
            return
        thread = self.folder_size_manager.start_calculate(path, item)
        if thread is not None:  # ：检查线程是否有效
            self.folder_threads[path] = thread  # 仅存储有效线程
    
    def _apply_hidden_style2(self, item, entry):
        """应用隐藏文件灰色显示样式"""
        try:
            if sys.platform == "win32":
                import win32api
                import win32con
                # Windows系统：使用文件属性判断
                is_hidden = win32api.GetFileAttributes(entry) & win32con.FILE_ATTRIBUTE_HIDDEN
            else:
                # Unix-like系统（Linux/macOS）：检查文件名是否以.开头
                is_hidden = os.path.basename(entry).startswith('.')
            # is_hidden = win32api.GetFileAttributes(entry) & win32con.FILE_ATTRIBUTE_HIDDEN
            if is_hidden:
                # print("隐藏文件")
                item.setForeground(0, QColor(Qt.GlobalColor.gray))

        except Exception:
            pass
    def _handle_folder_size_calculation2(self, entry, item):
        """处理文件夹大小异步计算及缓存"""
        folder_path = entry
        db_result = self.db.get_cached_size(folder_path)

        if db_result:
            cached_size, db_last_modified = db_result
            try:
                current_last_modified = os.path.getmtime(folder_path)
            except Exception:
                current_last_modified = 0
            
            if current_last_modified != db_last_modified:
                self.start_folder_size_thread(folder_path, item)
            else:
                item.setText(1, cached_size)
        else:
            self.start_folder_size_thread(folder_path, item)

    def _update_status_bar(self, file_count, folder_count):
        """更新状态栏信息（修改：使用翻译）"""
        if self.error_occurred:
            return
        total = file_count + folder_count
        # 从翻译获取状态文本模板（默认值原硬编码）
        status_template = self.translation.get(
            "status_text", 
            "{current_path} | 总数：{total} | 文件：{file_count} | 文件夹：{folder_count} | 选中：{selected_count}"
        )
        status_text = status_template.format(
            current_path=self.current_path,
            total=total,
            file_count=file_count,
            folder_count=folder_count,
            selected_count=len(self.file_list.selectedItems())
        )
        self.fm.status_bar.showMessage(status_text)

    def filter_files(self, keyword: str):
        """根据关键词过滤文件列表项，返回匹配数量"""
        match_count = 0
        for index in range(self.file_list.topLevelItemCount()):
            item = self.file_list.topLevelItem(index)
            file_name = item.text(0)
            if keyword in file_name:
                item.setHidden(False)
                match_count += 1
            else:
                item.setHidden(True)
        return match_count  # ：返回匹配的文件数量

    def clear_filter(self):
        """清除过滤，显示所有文件"""
        for index in range(self.file_list.topLevelItemCount()):
            item = self.file_list.topLevelItem(index)
            item.setHidden(False)

    def _update_filelist_from_thread(self, file_list: list):
        """异步扫描完成后更新文件列表（修改：使用翻译）"""
        self.file_list_data = file_list  # 缓存数据
        # 初始按默认方式排序（名称升序）
        sorted_file_list = sort_file_list(
            file_list,
            sort_key="name",  # 按名称排序（可选"size"/"mtime"）
            reverse=False
        )
        self.file_list.clear()  # 清除临时提示
        file_count = folder_count = 0
        for info in sorted_file_list:
            # 统计文件/文件夹数量（与原有逻辑一致）
            if info["is_dir"]:
                folder_count += 1
            else:
                file_count += 1
            # 创建列表项（复用 _create_list_item 逻辑）
            item = self._create_list_item_from_info(info)
            self._apply_hidden_style2(item, info["path"])  # 隐藏文件样式
            # 处理文件夹大小计算（与原有逻辑一致）
            if info["is_dir"] and self.show_all_sizes:
                self._handle_folder_size_calculation2(info["path"], item)
        self._update_status_bar(file_count, folder_count)
        # 无文件时显示空提示（使用翻译）
        if file_count == 0 and folder_count == 0:
            # 替换为翻译文本（默认值"当前目录为空"）
            self.file_list.set_empty_hint(self.translation.get("empty_dir_hint", "当前目录为空"))
        else:
            self.file_list.set_empty_hint("")
    def _update_filelist_from_sorted(self,filelist2:list):
        """
        从排序后的文件列表更新UI，用于过滤后的显示。
        :param filelist2: 已排序的文件列表数据
        """
        if filelist2:
            # self._setup_header_layout()
            self.file_list.clear()
            for info in filelist2:
                # 创建列表项（复用 _create_list_item 逻辑）
                item = self._create_list_item_from_info(info)
                self._apply_hidden_style2(item, info["path"])  # 隐藏文件样式
                # 新增：处理文件夹大小计算（与_update_filelist_from_thread逻辑一致）
                if info["is_dir"] and self.show_all_sizes:
                    self._handle_folder_size_calculation2(info["path"], item)
                # 关键新增：清空旧列表项（避免重复显示）
                self.file_list.addTopLevelItem(item)
    def _create_list_item_from_info_child(self, info: dict):
        """适配异步扫描结果的列表项创建（新增数据存储）"""
        file_type = 'folder' if info["is_dir"] else get_file_type(info["name"])
        size = self.translation.get("folder", "<文件夹>") if (info["is_dir"] and not self.show_all_sizes) else format_size(info["size"])
        if info["is_dir"] and self.show_all_sizes:
            size = self.translation.get("calculating", "计算中")
        
        item = QTreeWidgetItem([info["name"], size])
        item.setIcon(0, self.icons.get(file_type, self.icons['default']))
        
        # 关键调整：从扫描结果获取是否有子目录（需扫描器返回该字段）
        if info["is_dir"]:
            item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
            item.setData(0, Qt.UserRole, info["path"])  # 存储路径
        
        # 新增：设置工具提示（原代码位置错误）
        item.setToolTip(0, info["name"])
        
        # 新增：处理修改时间列（原代码位置错误）
        if self.show_mtime:
            import datetime
            if info["mtime"]:
                # 格式化时间戳为可读格式（如 "2024-06-01 12:34"）
                mtime_str = datetime.datetime.fromtimestamp(info["mtime"]).strftime("%Y-%m-%d %H:%M")
                item.setText(2, mtime_str)  # 设置第三列内容
        
        return item
    def _create_list_item_from_info(self, info: dict):
        """适配异步扫描结果的列表项创建（新增数据存储）"""
        file_type = 'folder' if info["is_dir"] else get_file_type(info["name"])
        size = self.translation.get("folder", "<文件夹>") if (info["is_dir"] and not self.show_all_sizes) else format_size(info["size"])
        if info["is_dir"] and self.show_all_sizes:
            size = self.translation.get("calculating", "计算中")
        
        item = QTreeWidgetItem(self.file_list, [info["name"], size])
        item.setIcon(0, self.icons.get(file_type, self.icons['default']))
        
        # 关键调整：从扫描结果获取是否有子目录（需扫描器返回该字段）
        if info["is_dir"]:
            item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
            item.setData(0, Qt.UserRole, info["path"])  # 存储路径
        
        # 新增：设置工具提示（原代码位置错误）
        item.setToolTip(0, info["name"])
        
        # 新增：处理修改时间列（原代码位置错误）
        if self.show_mtime:
            import datetime
            if info["mtime"]:
                # 格式化时间戳为可读格式（如 "2024-06-01 12:34"）
                mtime_str = datetime.datetime.fromtimestamp(info["mtime"]).strftime("%Y-%m-%d %H:%M")
                item.setText(2, mtime_str)  # 设置第三列内容
        
        return item
    def _handle_scan_error(self, error_msg):
        # 显示错误提示（使用翻译）
        error_text = self.translation.get("scan_error", "当前目录扫描错误：{error_msg}").format(error_msg=error_msg)
        self.fm.status_bar.showMessage(error_text)
        self.error_occurred = True
        
        
        # 新增：绑定文件夹展开事件（`FileListUpdater`初始化）
        # 新增：记录已加载子目录的路径（避免重复加载）
        self.loaded_subdirs = set()
        # 新增：绑定文件夹展开事件
        self.file_list.itemExpanded.connect(self.on_folder_expanded)

    def on_folder_expanded(self, item):
        """文件夹项展开时加载子目录（优化：已加载时直接展开）"""
        folder_path = item.data(0, Qt.UserRole)  # 从UserRole获取存储的路径
        # print(f"[调试] 尝试展开文件夹：{folder_path}")  # 新增：打印展开的路径
        if not folder_path:
            # print(f"[调试] 无效路径，跳过展开")  # 新增：路径为空时提示
            return
        
        # 关键修改：检查是否已加载且存在子节点
        if folder_path in self.loaded_subdirs:
            if item.childCount() > 0:
                # print(f"[调试] 已加载过子目录且存在子节点，直接展开：{folder_path}")
                item.setExpanded(True)  # 显式展开节点
                return
            # else:
                # print(f"[调试] 已加载过子目录但无内容，重新加载：{folder_path}")
        
        # 显示加载中提示（使用翻译）
        item.setText(1, self.translation.get("calculating", "计算中..."))
        
        # 关键修改：使用弱引用保存item，避免强引用导致对象无法销毁
        weak_item = weakref.ref(item)
        self.file_list_loader.start_load_subdir(
            parent_path=folder_path,
            show_hidden=self.show_hidden,
            callback=lambda sub_list: self._on_subdir_loaded(sub_list, weak_item)
        )

    def _on_subdir_loaded(self, sub_list: list, weak_parent_item):
        """子目录加载完成后更新UI（新增弱引用有效性检查）"""
        # 关键修改：通过弱引用获取实际对象，若已销毁则跳过
        parent_item = weak_parent_item()
        if not parent_item:
            return  # 对象已销毁，直接返回
        
        parent_path = parent_item.data(0, Qt.UserRole)
        self.loaded_subdirs.add(parent_path)
        
        # 恢复原大小显示（使用翻译）
        parent_item.setText(1, self.translation.get("folder", "<文件夹>"))
        
        # 关键新增：清除父节点原有的所有子节点（避免重复）
        parent_item.takeChildren()  # 移除旧子节点
        
        # 使用当前全局排序规则对子目录内容排序
        sorted_sub_list = sort_file_list(
            sub_list,
            sort_key=self.header_handler.current_sort_key,  # 从排序处理器获取当前排序键
            reverse=self.header_handler.current_reverse      # 从排序处理器获取当前排序方向
        )
        
        # 遍历排序后的子目录数据，添加为父项的子节点
        for sub_info in sorted_sub_list:
            sub_item = self._create_list_item_from_info_child(sub_info)
            self._apply_hidden_style2(sub_item, sub_info["path"])
            parent_item.addChild(sub_item)  # 保持层级关系
        
        parent_item.setExpanded(True)  # 展开父项显示子节点
