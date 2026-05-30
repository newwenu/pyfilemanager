from PySide6.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QMutex, QMutexLocker
from utils.time_utils import get_file_mtime, format_mtime_timestamp_full
from utils.allocation_size_utils import get_size_info_for_display, get_directory_allocations, _get_filesystem_block_size
import os
import sys
from utils.size_utils import format_size


# 异步获取文件占用空间（Size on Disk）的线程
class AllocationSizeThread(QThread):
    """异步获取文件实际占用磁盘空间"""
    allocation_size_calculated = Signal(dict)  # 发送包含大小信息的字典
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self._is_running = True

    def run(self):
        if not self._is_running:
            return
        # 获取包含精度信息的大小数据
        size_info = get_size_info_for_display(self.file_path)
        if self._is_running:
            self.allocation_size_calculated.emit(size_info)
    
    def stop(self):
        """安全停止线程"""
        self._is_running = False
        self.wait(100)  # 等待最多100ms


# 异步计算文件夹实际占用空间的线程（被动查询模式）
class FolderAllocationSizeThread(QThread):
    """异步计算文件夹实际占用磁盘空间（Size on Disk）
    
    采用被动查询模式：
    - 计算线程只更新共享数据，不主动发送信号
    - UI 通过定时器主动查询进度
    - 计算线程无阻塞，最大化性能
    """
    calculation_finished = Signal()  # 仅通知计算完成
    
    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self._is_running = True
        
        # 共享数据（线程安全）
        self._mutex = QMutex()
        self._total_logical = 0
        self._total_allocation = 0
        self._file_count = 0
        self._permission_errors = 0
        self._is_complete = False

    def get_progress(self):
        """获取当前进度（线程安全）"""
        with QMutexLocker(self._mutex):
            return (
                self._total_logical,
                self._total_allocation,
                self._file_count,
                self._permission_errors,
                self._is_complete
            )

    def _flush_progress(self, total_logical, total_allocation, file_count, permission_errors):
        """批量更新共享进度数据"""
        with QMutexLocker(self._mutex):
            self._total_logical = total_logical
            self._total_allocation = total_allocation
            self._file_count = file_count
            self._permission_errors = permission_errors

    def run(self):
        """递归计算文件夹大小，只更新共享数据"""
        UPDATE_INTERVAL = 500
        total_logical = 0
        total_allocation = 0
        file_count = 0
        permission_errors = 0
        
        # Windows 预取簇大小，避免每文件 API 调用
        if sys.platform == 'win32':
            cluster_size = _get_filesystem_block_size(self.folder_path)
        else:
            cluster_size = 4096
        
        try:
            # 使用栈实现递归，避免递归深度限制
            dirs_to_scan = [self.folder_path]
            
            while dirs_to_scan and self._is_running:
                current_dir = dirs_to_scan.pop()
                
                # Windows: 批量查询当前目录所有文件的分配大小（一次 NtQueryDirectoryFile）
                if sys.platform == 'win32':
                    dir_alloc_map = get_directory_allocations(current_dir)
                
                try:
                    # 使用 os.scandir 比 os.listdir 更快，且直接返回 stat 信息
                    with os.scandir(current_dir) as entries:
                        for entry in entries:
                            if not self._is_running:
                                return
                            
                            try:
                                if entry.is_file(follow_symlinks=False):
                                    file_stat = entry.stat(follow_symlinks=False)
                                    logical_size = file_stat.st_size
                                    total_logical += logical_size
                                    
                                    # 分配大小（平台特定）
                                    if sys.platform == 'win32':
                                        # 优先从批量查询结果中取
                                        alloc_size = dir_alloc_map.get(entry.name)
                                        if alloc_size is None:
                                            # fallback: 簇对齐估算
                                            alloc_size = ((logical_size + cluster_size - 1) // cluster_size) * cluster_size
                                    else:
                                        # Linux/Mac: 使用 st_blocks * 512
                                        if hasattr(file_stat, 'st_blocks') and file_stat.st_blocks > 0:
                                            alloc_size = file_stat.st_blocks * 512
                                        else:
                                            alloc_size = logical_size
                                    
                                    total_allocation += alloc_size
                                    file_count += 1
                                    
                                    # 批量更新共享数据，减少锁竞争
                                    if file_count % UPDATE_INTERVAL == 0:
                                        self._flush_progress(
                                            total_logical, total_allocation,
                                            file_count, permission_errors
                                        )
                                    
                                elif entry.is_dir(follow_symlinks=False):
                                    # 将子目录加入扫描队列
                                    dirs_to_scan.append(entry.path)
                                    
                            except PermissionError:
                                permission_errors += 1
                                continue
                            except OSError:
                                continue
                                
                except PermissionError:
                    permission_errors += 1
                    continue
                except OSError:
                    continue
            
            # 计算完成，标记状态
            if self._is_running:
                with QMutexLocker(self._mutex):
                    self._total_logical = total_logical
                    self._total_allocation = total_allocation
                    self._file_count = file_count
                    self._permission_errors = permission_errors
                    self._is_complete = True
                self.calculation_finished.emit()
                
        except Exception as e:
            # 发生错误，标记完成
            if self._is_running:
                with QMutexLocker(self._mutex):
                    self._is_complete = True
                self.calculation_finished.emit()
    
    def stop(self):
        """安全停止线程"""
        self._is_running = False
        self.wait(500)  # 等待最多500ms让线程退出


class FilePropertiesDialog(QDialog):
    def __init__(self, parent, file_path):
        super().__init__(parent)
        self.parent = parent
        self.file_path = file_path
        self.setWindowTitle(self.parent.translation.get("properties", "文件属性"))
        
        # 线程引用（用于清理）
        self._allocation_thread = None
        self._folder_thread = None
        
        # UI 查询定时器
        self._query_timer = QTimer(self)
        self._query_timer.timeout.connect(self._query_folder_progress)
        
        self._setup_ui()
        self._load_file_info()

    @staticmethod
    def show_for_selected_item(parent):
        selected = parent.file_list.selectedItems()
        if not selected:
            return
        item = selected[0]
        file_path = os.path.join(parent.current_path, item.text(0))
        dialog = FilePropertiesDialog(parent, file_path)
        dialog.exec()

    def _setup_ui(self):
        self.layout = QGridLayout(self)
        self.name_label = QLabel()
        self.path_label = QLabel()
        self.size_label = QLabel()
        self.mtime_label = QLabel()
        self.btn_ok = QPushButton(self.parent.translation.get("confirm", "确定"))
        self.btn_ok.clicked.connect(self.accept)
        
        self.layout.addWidget(QLabel(self.parent.translation.get("name", "名称:")), 0, 0)
        self.layout.addWidget(self.name_label, 0, 1)
        self.layout.addWidget(QLabel(self.parent.translation.get("path", "路径:")), 1, 0)
        self.layout.addWidget(self.path_label, 1, 1)
        self.layout.addWidget(QLabel(self.parent.translation.get("size", "大小:")), 2, 0)
        self.layout.addWidget(self.size_label, 2, 1)
        self.layout.addWidget(QLabel(self.parent.translation.get("mtime", "修改时间:")), 3, 0)
        self.layout.addWidget(self.mtime_label, 3, 1)
        self.layout.addWidget(self.btn_ok, 4, 1, Qt.AlignmentFlag.AlignRight)

    def _load_file_info(self):
        """加载文件信息并启动异步计算"""
        try:
            # 立即获取可快速读取的属性
            mtime_timestamp = get_file_mtime(self.file_path)
            mtime_str = format_mtime_timestamp_full(mtime_timestamp)
            self.name_label.setText(os.path.basename(self.file_path))
            self.path_label.setText(self.file_path)
            self.mtime_label.setText(mtime_str)

            if os.path.isfile(self.file_path):
                # 文件：启动线程获取占用空间
                self.size_label.setText(self.parent.translation.get("size_calculating", "大小计算中..."))
                self._allocation_thread = AllocationSizeThread(self.file_path)
                self._allocation_thread.allocation_size_calculated.connect(
                    self._update_file_size, 
                    type=Qt.ConnectionType.QueuedConnection
                )
                self._allocation_thread.start()
            else:
                # 文件夹：启动线程计算实际占用空间（被动查询模式）
                self.size_label.setText(self.parent.translation.get("size_calculating", "正在扫描文件夹..."))
                self._folder_thread = FolderAllocationSizeThread(self.file_path)
                self._folder_thread.calculation_finished.connect(self._on_folder_finished)
                self._folder_thread.start()
                # 启动 UI 查询定时器（每 100ms 查询一次）
                self._query_timer.start(100)

        except Exception as e:
            self.parent.show_error("错误", f"获取属性失败: {str(e)}")
            self.close()

    def _query_folder_progress(self):
        """UI 主动查询文件夹计算进度"""
        if not self._folder_thread:
            return
        
        # 获取当前进度
        logical_bytes, allocation_bytes, file_count, permission_errors, is_complete = \
            self._folder_thread.get_progress()
        
        # 更新显示
        self._update_folder_display(
            logical_bytes, allocation_bytes, 
            file_count, permission_errors, is_complete
        )
        
        # 如果计算完成，停止定时器
        if is_complete:
            self._query_timer.stop()

    def _on_folder_finished(self):
        """计算完成回调"""
        self._query_timer.stop()
        # 最后一次查询确保显示最终值
        self._query_folder_progress()
        # 清理线程引用
        if self._folder_thread:
            self._folder_thread.deleteLater()
            self._folder_thread = None

    def _update_folder_display(self, logical_bytes, allocation_bytes, file_count, permission_errors, is_complete):
        """更新文件夹大小显示"""
        logical_formatted = format_size(logical_bytes)
        allocation_formatted = format_size(allocation_bytes)
        
        # 构建状态文本
        if permission_errors > 0:
            error_text = f", {permission_errors} 个文件无权限"
        else:
            error_text = ""
        
        if is_complete:
            # 计算完成
            size_text = f"{logical_formatted} (占用空间: {allocation_formatted}, {file_count} 个文件{error_text})"
        else:
            # 计算中，显示进度
            size_text = f"计算中... {logical_formatted} (占用: {allocation_formatted}, {file_count} 个文件{error_text})"
        
        self.size_label.setText(size_text)

    def _update_file_size(self, size_info):
        """更新文件大小显示"""
        logical_formatted = size_info.get('logical_formatted', '未知')
        allocation_formatted = size_info.get('allocation_formatted', '未知')
        is_accurate = size_info.get('allocation_accurate', False)
        
        if is_accurate:
            size_text = f"{logical_formatted} (占用空间: {allocation_formatted})"
        else:
            size_text = f"{logical_formatted} (占用空间: ~{allocation_formatted})"
        
        self.size_label.setText(size_text)
        
        # 清理线程引用
        if self._allocation_thread:
            self._allocation_thread.deleteLater()
            self._allocation_thread = None

    def closeEvent(self, event):
        """对话框关闭时安全停止所有线程"""
        self._stop_all_threads()
        event.accept()
    
    def reject(self):
        """用户取消时停止线程"""
        self._stop_all_threads()
        super().reject()
    
    def _stop_all_threads(self):
        """安全停止所有运行中的线程"""
        # 停止查询定时器
        if self._query_timer.isActive():
            self._query_timer.stop()
        
        # 停止文件线程
        if self._allocation_thread and self._allocation_thread.isRunning():
            self._allocation_thread.stop()
            self._allocation_thread = None
        
        # 停止文件夹线程
        if self._folder_thread and self._folder_thread.isRunning():
            self._folder_thread.stop()
            self._folder_thread = None
