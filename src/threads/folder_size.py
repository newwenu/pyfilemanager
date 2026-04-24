import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QThread, Signal, QObject, QRunnable, QThreadPool
from PySide6.QtWidgets import QTreeWidgetItem
from utils.logging_config import get_logger
from utils.size_utils import format_size
from dbload_manager.file_tree_manager import CacheValidity

logger = get_logger(__name__)


class FolderSizeThread(QThread):
    """计算文件夹大小的线程 - 支持动态深度调整和增量缓存"""
    # 修改为发送原始字节数和格式化大小
    # 使用 object 类型避免大整数溢出（Python int 可以表示任意大小）
    size_updated = Signal(str, object, str)  # (文件夹路径, 原始字节数, 格式化后的大小)

    # 配置参数 - 动态深度调整
    # 根据子项数目决定该层是否缓存及后续深度
    ITEM_COUNT_THRESHOLDS = {
        'very_high': 500,   # >500 子项：不缓存该层，停止深入
        'high': 200,        # 200-500 子项：缓存该层，但不深入
        'medium': 50,       # 50-200 子项：缓存该层，最多再深入1层
        'low': 10,          # 10-50 子项：缓存该层，最多再深入2层
        'very_low': 0       # <10 子项：缓存该层，最多再深入3层
    }
    MAX_TOTAL_CACHE_COUNT = 1000  # 总缓存数量限制
    BATCH_CACHE_SIZE = 50  # 每批缓存的子文件夹数量

    # 保护机制参数
    MAX_CALCULATION_TIME = 30  # 最大计算时间（秒）
    MAX_FOLDERS_TO_PROCESS = 10000  # 最大处理文件夹数
    UI_UPDATE_INTERVAL = 0.05  # UI更新间隔（秒）

    def __init__(self, path, file_tree_manager=None):
        super().__init__()
        self.path = path
        self._is_running = True
        self._terminate_requested = False
        self.file_tree_manager = file_tree_manager
        self._subfolder_sizes = {}
        self._cached_count = 0
        self._count_limit_reached = False
        # 动态深度控制：记录每个文件夹的剩余可深入层数
        self._remaining_depth = {}  # {folder_path: 剩余可深入层数}
        # 性能监控
        self._start_time = 0
        self._processed_count = 0
        self._last_update_time = 0
        self._failed_folders = []

    def run(self):
        # 注意：这里暂时无法传入 file_tree_manager，因为线程是独立的
        # 子文件夹缓存将在 FolderSizeManager._on_size_updated 中处理
        total_size = self.calculate_folder_size(self.path)
        if self._is_running:
            if total_size == -1:
                logger.debug(f"路径无法访问: {self.path}")
                self.size_updated.emit(self.path, -1, "unaccessable")
            else:
                formatted_size = format_size(total_size)
                self.size_updated.emit(self.path, total_size, formatted_size)

    def stop(self):
        """增强终止逻辑"""
        self._is_running = False
        self._terminate_requested = True
        # 等待线程结束，但最多等待10秒
        if not self.wait(10000):
            logger.warning(f"FolderSizeThread 未及时终止，强制终止")
            self.terminate()
            self.wait(2000)

    def calculate_folder_size(self, path):
        """
        计算文件夹总大小（字节数）- 支持动态深度调整和增量缓存（流式处理版本）

        使用流式处理，避免一次性加载所有文件夹信息到内存。
        采用后序遍历方式，先计算子文件夹大小，再计算父文件夹。

        Args:
            path: 文件夹路径

        Returns:
            总大小（字节），-1 表示无法访问
        """
        # 初始化性能监控
        self._start_time = time.time()
        self._processed_count = 0
        self._last_update_time = self._start_time
        self._failed_folders.clear()

        try:
            # 验证目录权限
            try:
                os.listdir(path)
            except PermissionError:
                logger.debug(f"根目录 {path} 无读取权限")
                return -1

            # 重置状态
            self._subfolder_sizes.clear()
            self._cached_count = 0
            self._count_limit_reached = False
            self._remaining_depth.clear()

            # 使用栈实现后序遍历，避免递归深度问题
            # 栈元素: (文件夹路径, 状态, 直接文件大小, 文件数, 子文件夹列表)
            # 状态: 0=待处理, 1=子文件夹已处理
            stack = [(path, 0, 0, 0, [])]
            # 存储子文件夹信息的临时字典
            folder_results = {}

            while stack and self._is_running and not self._terminate_requested:
                # 检查超时
                if time.time() - self._start_time > self.MAX_CALCULATION_TIME:
                    logger.warning(f"计算超时（>{self.MAX_CALCULATION_TIME}秒），返回部分结果")
                    break

                # 检查数量限制
                if self._processed_count >= self.MAX_FOLDERS_TO_PROCESS:
                    logger.warning(f"达到最大处理数量限制（{self.MAX_FOLDERS_TO_PROCESS}）")
                    break

                current_path, state, files_size, file_count, subfolders = stack[-1]

                if state == 0:
                    # 第一次访问：计算直接文件大小并准备处理子文件夹
                    stack[-1] = (current_path, 1, files_size, file_count, subfolders)

                    try:
                        # 获取目录内容
                        entries = list(os.scandir(current_path))
                        dirs = [e for e in entries if e.is_dir(follow_symlinks=False)]
                        files = [e for e in entries if e.is_file(follow_symlinks=False)]

                        # 计算直接文件大小
                        current_files_size = 0
                        current_file_count = len(files)

                        for entry in files:
                            try:
                                current_files_size += max(entry.stat().st_size, 0)
                            except (PermissionError, OSError) as e:
                                logger.debug(f"无法访问文件 {entry.path}: {e}")

                        # 更新栈顶信息
                        stack[-1] = (current_path, 1, current_files_size, current_file_count,
                                   [d.path for d in dirs])

                        # 评估是否深入子文件夹
                        item_count = len(files) + len(dirs)
                        should_cache, stop_deeper = self._evaluate_folder_for_cache(
                            current_path, item_count
                        )

                        if stop_deeper:
                            # 停止深入：需要计算子文件夹的大小并累加
                            for dir_entry in dirs:
                                if self._is_running and not self._terminate_requested:
                                    try:
                                        sub_size = self._quick_calculate_folder_size(dir_entry.path)
                                        if sub_size >= 0:
                                            current_files_size += sub_size
                                            current_file_count += 1  # 简化为计数文件夹
                                    except Exception as e:
                                        logger.debug(f"快速计算子文件夹失败 {dir_entry.path}: {e}")
                            # 更新栈顶信息（包含子文件夹大小）
                            stack[-1] = (current_path, 1, current_files_size, current_file_count, [])
                        else:
                            # 不停止深入：将子文件夹压入栈继续处理
                            for dir_entry in reversed(dirs):  # 反转保持顺序
                                if self._is_running and not self._terminate_requested:
                                    stack.append((dir_entry.path, 0, 0, 0, []))

                    except (PermissionError, OSError) as e:
                        logger.debug(f"无法访问文件夹 {current_path}: {e}")
                        self._failed_folders.append((current_path, str(e)))
                        stack.pop()
                        folder_results[current_path] = (0, 0, 0)  # 大小, 文件数, 文件夹数
                        continue

                else:
                    # 第二次访问：子文件夹已处理，计算总大小
                    stack.pop()
                    self._processed_count += 1

                    # 累加所有子文件夹的大小
                    total_size = files_size
                    total_file_count = file_count
                    total_folder_count = len(subfolders)

                    for subfolder in subfolders:
                        if subfolder in folder_results:
                            sub_size, sub_files, sub_folders = folder_results[subfolder]
                            total_size += sub_size
                            total_file_count += sub_files
                            total_folder_count += sub_folders

                    # 存储结果
                    folder_results[current_path] = (total_size, total_file_count, total_folder_count)

                    # 检查是否应该缓存
                    item_count = file_count + len(subfolders)
                    should_cache, _ = self._evaluate_folder_for_cache(current_path, item_count)

                    if should_cache:
                        self._subfolder_sizes[current_path] = {
                            'size': total_size,
                            'file_count': total_file_count,
                            'folder_count': total_folder_count
                        }

                        # 增量缓存
                        if len(self._subfolder_sizes) >= self.BATCH_CACHE_SIZE:
                            self._flush_cache_batch()

                    # UI 更新和让出时间片
                    self._yield_if_needed()

            # 获取根目录结果
            if path in folder_results:
                total_size, self._file_count, self._folder_count = folder_results[path]
            else:
                total_size, self._file_count, self._folder_count = 0, 0, 0

            # 刷新剩余缓存
            if self._subfolder_sizes:
                self._flush_cache_batch()

            # 记录统计信息
            elapsed = time.time() - self._start_time
            if self._failed_folders:
                logger.info(f"文件夹计算完成: {path}, "
                          f"处理 {self._processed_count} 个文件夹, "
                          f"失败 {len(self._failed_folders)} 个, "
                          f"耗时 {elapsed:.2f}s")

            return total_size

        except Exception as e:
            logger.error(f"计算文件夹大小时出错 {path}: {e}")
            return -1

    def _yield_if_needed(self):
        """
        根据需要让出时间片，避免阻塞UI

        基于时间间隔决定是否让出时间片，比基于计数器更精确
        """
        current_time = time.time()
        if current_time - self._last_update_time >= self.UI_UPDATE_INTERVAL:
            QThread.msleep(1)  # 让出1毫秒
            self._last_update_time = current_time

    def _quick_calculate_folder_size(self, path: str) -> int:
        """
        快速计算文件夹大小（不缓存，不深入控制）

        用于当停止深入时，仍然需要获取子文件夹的大小。
        使用简单的 os.walk 遍历，不记录中间结果。

        Args:
            path: 文件夹路径

        Returns:
            文件夹大小（字节），-1 表示无法访问
        """
        total_size = 0
        try:
            for current_path, dirs, files in os.walk(path, followlinks=False):
                if self._terminate_requested or not self._is_running:
                    return 0

                for file in files:
                    try:
                        file_path = os.path.join(current_path, file)
                        if sys.platform == "win32" and not file_path.startswith("\\\\?\\") and len(file_path) > 255:
                            file_path = f"\\\\?\\{file_path}"
                        total_size += max(os.path.getsize(file_path), 0)
                    except (PermissionError, OSError):
                        pass

                # 让出时间片
                if len(files) > 100:  # 只有文件较多时才让出
                    QThread.msleep(0)

            return total_size
        except Exception as e:
            logger.debug(f"快速计算文件夹大小失败 {path}: {e}")
            return -1

    def _evaluate_folder_for_cache(self, folder_path: str, item_count: int) -> tuple:
        """
        评估文件夹是否应该缓存，并决定是否停止深入

        根据子项数目动态调整策略（真正实现 ITEM_COUNT_THRESHOLDS）：
        - >500 子项：不缓存，停止深入（剩余深度=0）
        - 200-500 子项：缓存，停止深入（剩余深度=0）
        - 50-200 子项：缓存，允许再深入1层（剩余深度=1）
        - 10-50 子项：缓存，允许再深入2层（剩余深度=2）
        - <10 子项：缓存，允许再深入3层（剩余深度=3）

        子文件夹继承父文件夹的剩余深度-1，当剩余深度<=0时停止深入。

        Args:
            folder_path: 文件夹路径
            item_count: 子项数目（文件+文件夹）

        Returns:
            (should_cache, stop_deeper)
            should_cache: 是否缓存该文件夹
            stop_deeper: 是否停止深入缓存
        """
        # 检查总数量限制
        if self._cached_count >= self.MAX_TOTAL_CACHE_COUNT:
            if not self._count_limit_reached:
                self._count_limit_reached = True
                logger.info(f"总缓存数量达到限制 {self.MAX_TOTAL_CACHE_COUNT}")
            return False, True

        # 根据子项数目决定策略
        thresholds = self.ITEM_COUNT_THRESHOLDS

        if item_count > thresholds['very_high']:
            # >500 子项：不缓存，停止深入
            self._remaining_depth[folder_path] = 0
            return False, True
        elif item_count > thresholds['high']:
            # 200-500 子项：缓存，停止深入
            self._remaining_depth[folder_path] = 0
            return True, True
        elif item_count > thresholds['medium']:
            # 50-200 子项：缓存，允许再深入1层
            self._remaining_depth[folder_path] = 1
            return True, False
        elif item_count > thresholds['low']:
            # 10-50 子项：缓存，允许再深入2层
            self._remaining_depth[folder_path] = 2
            return True, False
        else:
            # <10 子项：继承父目录的剩余深度-1，或默认3层
            parent_path = os.path.dirname(folder_path)
            parent_remaining = self._remaining_depth.get(parent_path, 3)
            remaining = max(0, parent_remaining - 1)
            self._remaining_depth[folder_path] = remaining
            should_stop = remaining <= 0
            return True, should_stop

    def _flush_cache_batch(self):
        """
        批量写入缓存

        将已记录的子文件夹大小批量写入数据库，然后清空缓冲区
        """
        if not self.file_tree_manager or not self._subfolder_sizes:
            return

        try:
            batch_count = 0
            for folder_path, info in list(self._subfolder_sizes.items()):
                try:
                    # 检查是否已有有效缓存
                    existing_info = self.file_tree_manager.get_folder_info(folder_path)
                    if existing_info.cache_status == CacheValidity.VALID:
                        continue

                    # 缓存子文件夹大小
                    self.file_tree_manager.update_folder_size(
                        folder_path=folder_path,
                        size=info['size'],
                        file_count=info['file_count'],
                        folder_count=info['folder_count']
                    )
                    batch_count += 1
                    self._cached_count += 1

                except Exception as e:
                    logger.debug(f"批量缓存子文件夹失败 {folder_path}: {e}")

            # 清空已处理的缓存
            self._subfolder_sizes.clear()

            if batch_count > 0:
                logger.debug(f"批量缓存了 {batch_count} 个子文件夹，总计 {self._cached_count}")

        except Exception as e:
            logger.error(f"批量缓存子文件夹时出错: {e}")

    def get_cache_stats(self) -> dict:
        """
        获取缓存统计信息

        Returns:
            {
                'cached_count': 已缓存数量,
                'count_limit_reached': 是否达到数量限制,
                'processed_count': 处理的文件夹总数,
                'failed_count': 处理失败的文件夹数,
                'elapsed_time': 耗时（秒）
            }
        """
        elapsed = time.time() - self._start_time if self._start_time > 0 else 0
        return {
            'cached_count': self._cached_count,
            'count_limit_reached': self._count_limit_reached,
            'processed_count': self._processed_count,
            'failed_count': len(self._failed_folders),
            'elapsed_time': round(elapsed, 2)
        }


class FolderSizeTreeThread(QThread):
    """递归计算整个文件夹树大小的线程"""
    # 发送每个子文件夹的大小信息
    tree_size_updated = Signal(str, object, str, int, int)  # (路径, 大小, 格式化大小, 文件数, 文件夹数)
    tree_calculation_finished = Signal(str, int)  # (根路径, 总文件夹数)

    def __init__(self, root_path: str):
        super().__init__()
        self.root_path = root_path
        self._is_running = True
        self._terminate_requested = False
        self._folder_count = 0

    def run(self):
        """递归计算整个树的大小"""
        try:
            total_folders = self._calculate_tree_sizes(self.root_path)
            self.tree_calculation_finished.emit(self.root_path, total_folders)
        except Exception as e:
            logger.error(f"树大小计算失败 {self.root_path}: {e}")
            self.tree_calculation_finished.emit(self.root_path, 0)

    def _calculate_tree_sizes(self, path: str) -> int:
        """递归计算文件夹树大小，返回处理的文件夹数"""
        if not self._is_running or self._terminate_requested:
            return 0

        folder_count = 0

        try:
            for current_path, dirs, files in os.walk(path, followlinks=False):
                if not self._is_running or self._terminate_requested:
                    return folder_count

                # 计算当前文件夹大小
                total_size = 0
                for file in files:
                    try:
                        file_path = os.path.join(current_path, file)
                        if sys.platform == "win32" and not file_path.startswith("\\\\?\\") and len(file_path) > 255:
                            file_path = f"\\\\?\\{file_path}"
                        total_size += max(os.path.getsize(file_path), 0)
                    except (OSError, PermissionError):
                        pass

                # 发送当前文件夹的大小信息
                formatted_size = format_size(total_size)
                self.tree_size_updated.emit(
                    current_path,
                    total_size,
                    formatted_size,
                    len(files),
                    len(dirs)
                )

                folder_count += 1

                # 每处理10个文件夹让出时间片
                if folder_count % 10 == 0:
                    QThread.msleep(1)

        except Exception as e:
            logger.error(f"计算树大小时出错 {path}: {e}")

        return folder_count

    def stop(self):
        """停止线程"""
        self._is_running = False
        self._terminate_requested = True
        # 等待线程结束，但最多等待10秒
        if not self.wait(10000):
            logger.warning(f"FolderSizeTreeThread 未及时终止，强制终止")
            self.terminate()
            self.wait(2000)


class FolderSizeSmartTreeThread(QThread):
    """
    智能树结构大小计算线程

    利用 FileTreeManager 的缓存机制，只计算需要更新的文件夹，
    避免重复计算已经缓存且有效的子文件夹。
    """
    # 信号：每个文件夹计算完成时发射
    folder_size_updated = Signal(str, object, str, int, int)  # (路径, 大小, 格式化大小, 文件数, 文件夹数)
    # 信号：计算完成时发射
    calculation_finished = Signal(str, dict)  # (根路径, 统计信息)

    def __init__(self, root_path: str, file_tree_manager):
        super().__init__()
        self.root_path = root_path
        self.file_tree_manager = file_tree_manager
        self._is_running = True
        self._terminate_requested = False

    def run(self):
        """执行智能树结构计算"""
        try:
            logger.info(f"开始智能计算: {self.root_path}")

            # 使用 FileTreeManager 的智能计算方法
            stats = self.file_tree_manager.update_folder_tree_sizes_smart(self.root_path)

            # 获取所有子文件夹的大小信息并发射信号
            subtree_info = self.file_tree_manager.get_subtree_size_info(self.root_path)

            for path, info in subtree_info.items():
                if not self._is_running or self._terminate_requested:
                    break

                self.folder_size_updated.emit(
                    path,
                    info['size'],
                    info['formatted_size'],
                    info['file_count'],
                    info['folder_count']
                )

            self.calculation_finished.emit(self.root_path, stats)
            logger.info(f"智能计算完成: {self.root_path}, 缓存命中率: {stats.get('cache_hit_rate', 0):.1f}%")

        except Exception as e:
            logger.error(f"智能树计算失败 {self.root_path}: {e}")
            self.calculation_finished.emit(self.root_path, {
                'total_folders': 0,
                'cached_used': 0,
                'recalculated': 0,
                'cache_hit_rate': 0,
                'error': str(e)
            })

    def stop(self):
        """停止计算"""
        self._is_running = False
        self._terminate_requested = True
        if self.file_tree_manager:
            self.file_tree_manager.stop_calculation()
        # 等待线程结束，但最多等待10秒
        if not self.wait(10000):
            logger.warning(f"FolderSizeSmartTreeThread 未及时终止，强制终止")
            self.terminate()
            self.wait(2000)


class DatabaseCacheWorker(QRunnable):
    """在后台线程中执行数据库缓存操作"""

    def __init__(self, file_tree_manager, path, raw_size, file_count, folder_count, thread_ref):
        super().__init__()
        self.file_tree_manager = file_tree_manager
        self.path = path
        self.raw_size = raw_size
        self.file_count = file_count
        self.folder_count = folder_count
        self.thread_ref = thread_ref
        self.setAutoDelete(True)

    def run(self):
        """在后台线程中执行缓存操作"""
        try:
            # 更新 FileTreeManager 缓存
            self.file_tree_manager.update_folder_size(
                folder_path=self.path,
                size=self.raw_size,
                file_count=self.file_count,
                folder_count=self.folder_count,
                scan_duration_ms=0
            )
            logger.info(f"FileTreeManager 缓存更新成功: {self.path} = {self.raw_size} bytes")

            # 缓存所有子文件夹的大小
            if self.thread_ref:
                self._cache_subfolder_sizes_from_thread(self.thread_ref)
        except Exception as e:
            logger.error(f"FileTreeManager 缓存更新失败: {self.path}, 错误: {str(e)}")

    def _cache_subfolder_sizes_from_thread(self, thread):
        """从线程中缓存所有子文件夹的大小"""
        if not thread:
            return

        try:
            # 刷新线程中剩余的缓存
            thread._flush_cache_batch()

            # 获取缓存统计信息
            stats = thread.get_cache_stats()
            if stats['cached_count'] > 0:
                limit_info = []
                if stats['count_limit_reached']:
                    limit_info.append(f"数量限制 {thread.MAX_TOTAL_CACHE_COUNT}")
                if stats['failed_count'] > 0:
                    limit_info.append(f"失败 {stats['failed_count']} 个")

                logger.info(f"子文件夹缓存完成: {stats['cached_count']} 个, "
                          f"处理 {stats['processed_count']} 个, "
                          f"耗时 {stats['elapsed_time']}s"
                          + (f" ({'，'.join(limit_info)})" if limit_info else ""))

        except Exception as e:
            logger.error(f"缓存子文件夹大小时出错: {e}")


class FolderSizeManager(QObject):
    """管理文件夹大小计算线程的管理器 - 整合 FileTreeManager"""
    size_updated = Signal(QTreeWidgetItem, str)  # (文件列表项, 格式化后的大小)
    # 新增：树结构计算信号
    tree_size_updated = Signal(str, object, str)  # (路径, 大小, 格式化大小)
    tree_calculation_finished = Signal(str, int)  # (根路径, 总文件夹数)
    # 新增：智能计算信号
    smart_calculation_finished = Signal(str, dict)  # (根路径, 统计信息)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.threads = {}
        self.wait_queue = []
        self.parent = parent
        # 从配置读取最大线程数，默认10
        self.max_threads = self._load_max_threads_from_config()
        # 使用新的 FileTreeManager
        self.file_tree_manager = parent.file_tree_manager if parent else None
        # 树结构计算线程
        self._tree_threads = {}
        # 数据库缓存线程池
        self._db_thread_pool = QThreadPool()
        self._db_thread_pool.setMaxThreadCount(2)  # 限制数据库操作线程数

    def _load_max_threads_from_config(self) -> int:
        """从配置加载最大线程数"""
        try:
            from core import get_service
            config_manager = get_service("config_manager")
            if config_manager:
                # 尝试读取配置，默认10
                max_threads = config_manager.get("folder_size.max_threads", 10)
                # 确保在合理范围内 (1-50)
                return max(1, min(50, int(max_threads)))
        except Exception as e:
            logger.debug(f"加载线程配置失败: {e}")
        return 10  # 默认10个线程

    def start_calculate(self, path: str, item: QTreeWidgetItem) -> FolderSizeThread:
        """启动文件夹大小计算线程

        Returns:
            FolderSizeThread: 启动的线程对象，如果加入等待队列或跳过则返回 None
        """
        if path in self.threads:
            logger.debug(f"路径 {path} 已存在计算线程，跳过")
            return None

        if len(self.threads) >= self.max_threads:
            logger.debug(f"线程数已达上限 ({len(self.threads)}/{self.max_threads})，路径 {path} 加入等待队列 (队列长度: {len(self.wait_queue)})")
            self.wait_queue.append((path, item))
            return None

        # 权限检查
        if not os.access(path, os.R_OK):
            logger.error(f"路径 {path} 无读取权限")
            self.size_updated.emit(item, self.parent.translation.get("no_permission", "无权限"))
            return None

        # 启动线程（传入 file_tree_manager 用于增量缓存）
        thread = FolderSizeThread(path, self.file_tree_manager)
        self.threads[path] = thread
        thread.size_updated.connect(lambda p, s, f: self._on_size_updated(p, s, f, item))
        thread.start()
        logger.debug(f"启动文件夹大小计算线程: {path} (当前活动线程: {len(self.threads)}/{self.max_threads})")
        return thread

    def _check_wait_queue(self):
        """检查等待队列，启动等待中的计算任务"""
        started_count = 0
        while self.wait_queue and len(self.threads) < self.max_threads:
            path, item = self.wait_queue.pop(0)
            logger.debug(f"从等待队列启动计算: {path} (剩余队列: {len(self.wait_queue)})")
            self.start_calculate(path, item)
            started_count += 1

        if started_count > 0:
            logger.info(f"从等待队列启动了 {started_count} 个计算任务")

    def _on_size_updated(self, path: str, raw_size: int, formatted_size: str, item: QTreeWidgetItem):
        """线程计算完成后的回调 - 使用 FileTreeManager 存储"""
        # 处理无法访问的情况
        if raw_size == -1:
            self.size_updated.emit(item, self.parent.translation.get("unaccessable", "无法访问"))
            # 标记为不可访问（使用后台线程避免阻塞UI）
            if self.file_tree_manager:
                worker = DatabaseCacheWorker(
                    self.file_tree_manager, path, -1, 0, 0, None
                )
                self._db_thread_pool.start(worker)
        else:
            self.size_updated.emit(item, formatted_size)

            # 使用 FileTreeManager 更新缓存（使用后台线程避免阻塞UI）
            if self.file_tree_manager:
                thread = self.threads.get(path)
                file_count = getattr(thread, '_file_count', 0) if thread else 0
                folder_count = getattr(thread, '_folder_count', 0) if thread else 0

                worker = DatabaseCacheWorker(
                    self.file_tree_manager, path, raw_size, file_count, folder_count, thread
                )
                self._db_thread_pool.start(worker)

            # 更新 file_list_data（快速操作，直接执行）
            self._update_file_list_data(path, raw_size, formatted_size)

        # 清理线程并检查等待队列
        if path in self.threads:
            completed_thread = self.threads[path]
            del self.threads[path]
            logger.debug(f"计算线程完成: {path} (剩余活动线程: {len(self.threads)}/{self.max_threads}, 等待队列: {len(self.wait_queue)})")
            self._check_wait_queue()

    def _update_file_list_data(self, path: str, raw_size: int, formatted_size: str):
        """更新 file_list_data"""
        try:
            file_list_updater = self.parent.file_list_updater
            # 线性搜索查找对应项
            for file_info in file_list_updater.file_list_data:
                if file_info.get("path") == path and file_info.get("is_dir"):
                    file_info["size"] = raw_size
                    file_info["raw_size"] = raw_size
                    file_info["display_size"] = formatted_size
                    logger.debug(f"更新 file_list_data: {path} -> {raw_size} bytes")
                    break
        except Exception as e:
            logger.error(f"更新 file_list_data 失败: {str(e)}")

    def get_thread_stats(self) -> dict:
        """获取线程统计信息

        Returns:
            {
                'active_threads': 活动线程数,
                'max_threads': 最大线程数,
                'wait_queue_size': 等待队列大小,
                'active_paths': 活动线程的路径列表
            }
        """
        return {
            'active_threads': len(self.threads),
            'max_threads': self.max_threads,
            'wait_queue_size': len(self.wait_queue),
            'active_paths': list(self.threads.keys())
        }

    def set_max_threads(self, max_threads: int) -> bool:
        """动态设置最大线程数

        Args:
            max_threads: 新的最大线程数 (1-50)

        Returns:
            bool: 是否设置成功
        """
        try:
            # 限制在合理范围内
            new_limit = max(1, min(50, int(max_threads)))
            old_limit = self.max_threads
            self.max_threads = new_limit

            logger.info(f"最大线程数已调整: {old_limit} -> {new_limit}")

            # 如果新的限制更大，立即检查等待队列
            if new_limit > old_limit:
                self._check_wait_queue()

            return True
        except Exception as e:
            logger.error(f"设置最大线程数失败: {e}")
            return False

    def start_tree_calculation(self, root_path: str) -> FolderSizeTreeThread:
        """
        启动递归计算整个文件夹树的大小

        Args:
            root_path: 根文件夹路径

        Returns:
            计算线程对象
        """
        if root_path in self._tree_threads:
            logger.debug(f"路径 {root_path} 已存在计算线程，跳过")
            return self._tree_threads[root_path]

        # 检查当前线程数是否超过限制
        if len(self._tree_threads) >= self.max_threads:
            logger.debug(f"树结构线程数已达上限，路径 {root_path} 加入等待队列")
            return None

        thread = FolderSizeTreeThread(root_path)
        self._tree_threads[root_path] = thread

        # 连接信号
        thread.tree_size_updated.connect(lambda p, s, f, fc, fol: self._on_tree_size_updated(p, s, f, fc, fol))
        thread.tree_calculation_finished.connect(lambda p, c: self._on_tree_calculation_finished(p, c))
        thread.finished.connect(lambda: self._cleanup_tree_thread(root_path))

        thread.start()
        return thread

    def _on_tree_size_updated(self, path: str, size: int, formatted_size: str, file_count: int, folder_count: int):
        """树结构计算过程中每个文件夹的回调"""
        # 更新 FileTreeManager 缓存
        if self.file_tree_manager:
            try:
                self.file_tree_manager.update_folder_size(
                    folder_path=path,
                    size=size,
                    file_count=file_count,
                    folder_count=folder_count
                )
            except Exception as e:
                logger.error(f"树结构缓存更新失败 {path}: {e}")

        # 发射信号通知UI更新
        self.tree_size_updated.emit(path, size, formatted_size)

    def _on_tree_calculation_finished(self, root_path: str, total_folders: int):
        """树结构计算完成的回调"""
        logger.info(f"树结构大小计算完成: {root_path}, 共 {total_folders} 个文件夹")
        self.tree_calculation_finished.emit(root_path, total_folders)

    def _cleanup_tree_thread(self, root_path: str):
        """清理树结构计算线程"""
        if root_path in self._tree_threads:
            thread = self._tree_threads[root_path]
            thread.deleteLater()
            del self._tree_threads[root_path]

    def start_smart_tree_calculation(self, root_path: str) -> 'FolderSizeSmartTreeThread':
        """
        启动智能树结构计算 - 利用缓存避免重复计算

        Args:
            root_path: 根文件夹路径

        Returns:
            计算线程对象
        """
        if root_path in self._tree_threads:
            logger.debug(f"路径 {root_path} 已在计算中")
            return self._tree_threads[root_path]

        thread = FolderSizeSmartTreeThread(root_path, self.file_tree_manager)
        self._tree_threads[root_path] = thread

        # 连接信号
        thread.folder_size_updated.connect(self._on_tree_size_updated)
        thread.calculation_finished.connect(self._on_tree_calculation_finished)
        thread.finished.connect(lambda: self._cleanup_tree_thread(root_path))

        thread.start()
        logger.info(f"启动智能树结构计算: {root_path}")
        return thread

    def stop_tree_calculation(self, root_path: str = None):
        """
        停止树结构计算

        Args:
            root_path: 要停止的路径，None 表示停止所有
        """
        if root_path:
            if root_path in self._tree_threads:
                self._tree_threads[root_path].stop()
        else:
            for thread in list(self._tree_threads.values()):
                thread.stop()
            self._tree_threads.clear()

    def stop_all_threads(self):
        """停止所有线程"""
        # 停止普通线程
        thread_count = len(self.threads)
        if thread_count > 0:
            logger.info(f"停止 {thread_count} 个普通线程")
            for thread in list(self.threads.values()):
                thread.stop()
                # 等待线程真正结束
                if not thread.wait(10000):  # 增加等待时间到10秒
                    logger.warning(f"线程未及时终止，强制终止")
                    thread.terminate()
                    thread.wait(2000)
            self.threads.clear()

        # 停止树结构线程
        tree_thread_count = len(self._tree_threads)
        if tree_thread_count > 0:
            logger.info(f"停止 {tree_thread_count} 个树结构线程")
            for thread in list(self._tree_threads.values()):
                thread.stop()
                # 等待线程真正结束
                if not thread.wait(10000):  # 增加等待时间到10秒
                    logger.warning(f"树结构线程未及时终止，强制终止")
                    thread.terminate()
                    thread.wait(2000)
            self._tree_threads.clear()
