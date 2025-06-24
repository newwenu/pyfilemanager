import os
from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtWidgets import QTreeWidgetItem
from utils.logging_config import get_logger  # 替换原 logging 导入

logger = get_logger(__name__)  # 通过日志模块获取记录器

class FolderSizeThread(QThread):
    """计算文件夹大小的线程"""
    size_updated = Signal(str, str)  # (文件夹路径, 格式化后的大小)

    def __init__(self, path):
        super().__init__()
        self.path = path
        self._is_running = True  # 退出标志
        self._terminate_requested = False  # 强制终止标记

    def run(self):
        total_size = self.calculate_folder_size(self.path)
        if self._is_running:  # 仅在未被终止时发送信号
            # 原生格式化逻辑（不依赖外部函数）
            units = ['B', 'KB', 'MB', 'GB', 'TB']
            unit_index = 0
            while total_size >= 1024 and unit_index < 4:
                total_size /= 1024
                unit_index += 1
            formatted_size = f'{total_size:.2f}{units[unit_index]}'
            self.size_updated.emit(self.path, formatted_size)

    def stop(self):
        """增强终止逻辑：设置双重标记并增加超时等待"""
        self._is_running = False
        self._terminate_requested = True  # 强制终止标记
        # 最多等待2秒，避免无限阻塞
        self.wait(2000)  # 2000ms超时

    def calculate_folder_size(self, path):
        total_size = 0
        for root, dirs, files in os.walk(path, followlinks=False):
            # 优先响应强制终止标记（避免os.walk阻塞）
            if self._terminate_requested or not self._is_running:
                return 0
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    total_size += max(os.path.getsize(file_path), 0)  # 防御性编程（避免负数）
                except PermissionError:
                    print(f"无权限访问文件: {file_path}")
                except Exception as e:
                    logger.error(f"计算文件 {file_path} 大小时出错：{str(e)}")
                    pass
        return total_size


class FolderSizeManager(QObject):
    """管理文件夹大小计算线程的管理器"""
    size_updated = Signal(QTreeWidgetItem, str)  # (文件列表项, 格式化后的大小)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.threads = {}  # 存储线程 {路径: 线程对象}

    def start_calculate(self, path: str, item: QTreeWidgetItem):
        """启动文件夹大小计算线程（避免重复计算）"""
        if path in self.threads:
            logger.debug(f"路径 {path} 已存在计算线程，跳过重复启动")  # 使用模块日志
            return  # 已存在同路径线程，跳过
        if not os.path.isdir(path):
            logger.error(f"路径 {path} 不是有效文件夹，无法启动计算")  # 使用模块日志
            return  # 路径无效，不启动线程
        if not os.access(path, os.R_OK):
            logger.error(f"路径 {path} 无读取权限，无法启动计算")  # 使用模块日志
            return
        if not os.access(path, os.W_OK):
            logger.error(f"路径 {path} 无写入权限，无法启动计算")  # 使用模块日志
            self.size_updated.emit(item, "无写入权限")
            return
        thread = FolderSizeThread(path)
        self.threads[path] = thread
        # 连接线程信号到管理器的回调（使用 lambda 绑定固定参数）
        thread.size_updated.connect(lambda p, s: self._on_size_updated(p, s, item))
        thread.start()

    def _on_size_updated(self, path: str, size: str, item: QTreeWidgetItem):
        """线程计算完成后的回调"""
        self.size_updated.emit(item, size)  # 触发 UI 更新信号
        # 写入数据库（优化异常处理）
        try:
            # ：获取最后修改时间时添加异常捕获
            try:
                last_modified = os.path.getmtime(path)
                if last_modified <= 0:
                    raise ValueError("无效时间戳")
            except Exception as e:
                # last_modified = 0  # 无效时间戳设为0（或根据业务需求调整）
                self.size_updated.emit(item, "读取出错")
                return -1
            self.parent().db.update_cache(
                folder_path=path,
                size=size,
                last_modified=last_modified
            )
            logger.info(f"数据库写入成功，路径：{path}，大小：{size}，最后修改时间：{last_modified}")
        except Exception as e:
            logger.error(f"数据库写入失败，路径：{path}，大小：{size}，错误信息：{str(e)}")
        if path in self.threads:
            del self.threads[path]  # 清理已完成的线程记录

    def stop_all_threads(self):
        """停止所有正在运行的线程"""
        thread_count = len(self.threads)
        if thread_count == 0:
            logger.info("无活跃线程需要停止")  # 使用模块日志
            return
        logger.info(f"开始停止 {thread_count} 个文件夹大小计算线程")  # 使用模块日志
        for thread in self.threads.values():
            thread.stop()
            thread.wait()  # 等待线程终止
        self.threads.clear()