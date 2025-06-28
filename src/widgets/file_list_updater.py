import os
from PySide6.QtWidgets import QTreeWidgetItem, QTreeWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from utils.file_utils import get_file_type, format_size
from dbload_manager.database_manager import DatabaseManager
import win32api
import win32con
from threads.file_list_loader import FileListLoaderManager  # 导入
from handlers.header_sort_handler import HeaderSortHandler  # 新增导入
from utils.sort_utils import sort_file_list  # 新增：导入排序工具
from utils.logging_config import get_logger
logger = get_logger(__name__)
class FileListUpdater:
    def __init__(self, fm):  # 仅传递主窗口实例
        self.fm = fm  # 持有主窗口引用
        self.folder_threads = {}  # 实例变量：在FileListUpdater内部维护线程字典
        # ：初始化异步加载管理器
        self.file_list_loader = FileListLoaderManager(self.fm)
        self.file_list_loader.list_loaded.connect(self._update_filelist_from_thread)
        self.file_list_loader.error_occurred.connect(self._handle_scan_error)  # 新增错误处理
        # 可选：连接进度信号（用于显示加载提示）
        # self.file_list_loader.progress_updated.connect(self._update_progress)
        # 新增：初始化排序处理器并连接表头事件
        self.header_handler = HeaderSortHandler(self)
        # self.fm.file_list.header().sectionClicked.connect(self.header_handler.on_header_clicked)
        # self.fm.file_list.header().sectionDoubleClicked.connect(self.header_handler.on_header_double_clicked)
        # 新增：缓存文件列表数据（用于排序）
        self.file_list_data = []  
        self.show_mtime = self.fm.config_manager.config.get("show_mtime", False)
        self.last_updated_path = None  # 新增：记录最后一次更新的路径
        self.error_occurred = False

        
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
        # self.file_list_loader.stop_all()  # 关键修改：终止所有未完成的扫描线程
        # self._clean_old_threads()    # 清理旧线程
        # 启动异步加载（传递当前路径和显示隐藏文件的配置）
        # self.file_list_loader.start_load(self.current_path, self.show_hidden)
        # 可选：显示加载中的提示（如“加载中...”）
        # self.file_list.setPlaceholderText("加载中...")
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
        """设置文件列表列布局"""
        if not self.current_path == '此电脑':
            # self.file_list.setHeaderLabels(["名称", "大小"])
            headers = ["名称", "大小"]
            # ：根据配置添加时间列
            if self.show_mtime:
                headers.append("修改时间")
                
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
    
    # def cleanup_threads(self):
    #     """供主窗口调用的线程清理接口"""
    #     for path, thread in list(self.folder_threads.items()):
    #         if thread is not None:  # ：跳过无效线程
    #             thread.stop()
    #             thread.wait()
    #             thread.deleteLater()
    #         del self.folder_threads[path]  # 无论是否有效都删除记录
    #     self.folder_threads.clear()

    # def _process_directory_entries(self):
    #     """处理目录扫描及条目创建"""
    #     file_count = folder_count = 0
    #     with os.scandir(self.current_path) as entries:
    #         for entry in entries:
    #             if not should_show(entry, self.show_hidden):
    #                 continue
                
    #             # 统计文件/文件夹数量
    #             if entry.is_dir():
    #                 folder_count += 1
    #             else:
    #                 file_count += 1

    #             # 创建列表项并设置基础属性
    #             item = self._create_list_item(entry)
    #             self._apply_hidden_style(item, entry)  # 处理隐藏文件样式
                
    #             # 处理文件夹大小异步计算
    #             if entry.is_dir() and self.show_all_sizes:
    #                 self._handle_folder_size_calculation(entry, item)
        
    #     return file_count, folder_count

    # def _create_list_item(self, entry):
    #     """创建文件/文件夹列表项"""
    #     file_type = 'folder' if entry.is_dir() else get_file_type(entry.name)
    #     size = '<文件夹>' if (entry.is_dir() and not self.show_all_sizes) else format_size(entry.stat().st_size)
    #     if entry.is_dir() and self.show_all_sizes:
    #         size = "计算中"  # 异步计算时显示占位符
        
    #     item = QTreeWidgetItem(self.file_list, [entry.name, size])
    #     item.setIcon(0, self.icons.get(file_type, self.icons['default']))
    #     item.setToolTip(0, entry.name)
    #     return item
    # def _apply_hidden_style(self, item, entry):
    #     """应用隐藏文件灰色显示样式"""
    #     try:
    #         is_hidden = win32api.GetFileAttributes(entry.path) & win32con.FILE_ATTRIBUTE_HIDDEN
    #         if is_hidden:
    #             # print("隐藏文件")
    #             item.setForeground(0, QColor(Qt.GlobalColor.gray))

    #     except Exception:
    #         pass
    def _apply_hidden_style2(self, item, entry):
        """应用隐藏文件灰色显示样式"""
        try:
            if sys.platform == "win32":
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
    # def _handle_folder_size_calculation(self, entry, item):
    #     """处理文件夹大小异步计算及缓存"""
    #     folder_path = entry.path
    #     db_result = self.db.get_cached_size(folder_path)

    #     if db_result:
    #         cached_size, db_last_modified = db_result
    #         try:
    #             current_last_modified = os.path.getmtime(folder_path)
    #         except Exception:
    #             current_last_modified = 0
            
    #         if current_last_modified != db_last_modified:
    #             self.start_folder_size_thread(folder_path, item)
    #         else:
    #             item.setText(1, cached_size)
    #     else:
    #         self.start_folder_size_thread(folder_path, item)

    def _update_status_bar(self, file_count, folder_count):
        """更新状态栏信息（需依赖主窗口的 status_bar，可通过回调传递）"""
        if self.error_occurred:
            return
        total = file_count + folder_count
        status_text = f"{self.current_path} | 总数：{total} | 文件：{file_count} | 文件夹：{folder_count} | 选中：{len(self.file_list.selectedItems())}"
        # 触发状态栏更新回调（需主窗口实现）
        self.fm.status_bar.showMessage(status_text)  # 直接通过主窗口访问状态栏
        
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
        """异步扫描完成后更新文件列表"""
        self.file_list_data = file_list  # 缓存数据
        # 初始按默认方式排序（名称升序）
        sorted_file_list = sort_file_list(
            file_list,
            sort_key="name",  # 按名称排序（可选"size"/"mtime"）
            reverse=False
        )
        # sorted_file_list = sort_file_list(
        # file_list, 
        # sort_key="name",  # 按名称排序（可选"size"/"mtime"）
        # reverse=False     # 升序（True为降序）
        # )
        # print(f"[Debug] 更新文件列表，包含 {len(self.sorted_file_list)} 项")
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
        # 无文件时显示空提示
        if file_count == 0 and folder_count == 0:
            self.file_list.set_empty_hint("当前目录为空")
        else:
            self.file_list.set_empty_hint("")
    def _update_filelist_from_sorted(self,filelist2:list):
        if filelist2:
            # self._setup_header_layout()
            self.file_list.clear()
            for info in filelist2:
                # 创建列表项（复用 _create_list_item 逻辑）
                item = self._create_list_item_from_info(info)
                self._apply_hidden_style2(item, info["path"])  # 隐藏文件样式
                # 关键新增：清空旧列表项（避免重复显示）
                self.file_list.addTopLevelItem(item)

    def _create_list_item_from_info(self, info: dict):
        """适配异步扫描结果的列表项创建（复用原有逻辑）"""
        file_type = 'folder' if info["is_dir"] else get_file_type(info["name"])
        size = '<文件夹>' if (info["is_dir"] and not self.show_all_sizes) else format_size(info["size"])
        if info["is_dir"] and self.show_all_sizes:
            size = "计算中"  # 异步计算时显示占位符
        item = QTreeWidgetItem(self.file_list, [info["name"], size])
        item.setIcon(0, self.icons.get(file_type, self.icons['default']))
        item.setToolTip(0, info["name"])
        if self.show_mtime:
            import datetime
            if info["mtime"]:
                # 格式化时间戳为可读格式（如 "2024-06-01 12:34"）
                mtime_str = datetime.datetime.fromtimestamp(info["mtime"]).strftime("%Y-%m-%d %H:%M")
                item.setText(2, mtime_str)  # 设置第三列内容
        return item
    def _handle_scan_error(self, error_msg):
        # 显示错误提示 （通过status_bar）
        # print(f"[Debug] 扫描错误：{error_msg}")
        self.fm.status_bar.showMessage(f"当前目录扫描错误：{error_msg}")
        self.error_occurred = True
