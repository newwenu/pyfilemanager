import os , sys
from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtWidgets import QTreeWidgetItem
from utils.logging_config import get_logger  # 替换原 logging 导入
from utils.size_parser import parse_formatted_size

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
            if total_size == -1:  # 新增：内容不可访问状态
                print(self.path,"unaccessable")
                self.size_updated.emit(self.path, "unaccessable")  # 发送状态标识
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
        try:
            # 增强：通过尝试读取目录内容验证根目录权限（替代os.access）
            try:
                os.listdir(path)  # 主动尝试读取目录内容（无权限会抛出PermissionError）
            except PermissionError:
                logger.debug(f"根目录 {path} 无读取权限，无法遍历")
                return -1  # 或返回-1标记无权限
            # logger.debug(f"开始遍历路径：{path}")  # 新增：记录遍历开始
            for root, dirs, files in os.walk(path, followlinks=False):
                # logger.debug(f"当前目录：{root}，文件数量：{len(files)}")
                # 优先响应强制终止标记（避免os.walk阻塞）
                if self._terminate_requested or not self._is_running:
                    return 0
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        if sys.platform == "win32" and not file_path.startswith("\\\\?\\") and len(file_path) > 255:
                            file_path = f"\\\\?\\{file_path}"  # 长路径处理
                        total_size += max(os.path.getsize(file_path), 0)
                        # 每处理10个文件休眠1ms（降低CPU占用）
                        if (len(files) % 10) == 0:
                            QThread.msleep(0)  # 需要导入QThread
                    except PermissionError:
                        logger.error(f"无权限访问文件: {file_path}")
                    except Exception as e:
                        logger.error(f"计算文件 {file_path} 大小时出错：{str(e)}")
                        pass
            return total_size
        except PermissionError as e:
            print(path,"unaccessable")
            logger.error(f"无法访问文件夹内容: {path}")
            return -1


class FolderSizeManager(QObject):
    """管理文件夹大小计算线程的管理器"""
    size_updated = Signal(QTreeWidgetItem, str)  # (文件列表项, 格式化后的大小)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.threads = {}  # 存储运行中的线程 {路径: 线程对象}
        self.wait_queue = []  # 等待队列（路径, item）
        self.max_threads = 10  # 最大同时运行线程数（可根据需求调整）
        self.parent = parent
        self.db = parent.db



    def start_calculate(self, path: str, item: QTreeWidgetItem):
        """启动文件夹大小计算线程（增加并发限制）"""
        if path in self.threads:
            logger.debug(f"路径 {path} 已存在计算线程，跳过重复启动")
            return
        # 检查当前线程数是否超过限制
        if len(self.threads) >= self.max_threads:
            logger.debug(f"当前线程数已达上限（{self.max_threads}），路径 {path} 加入等待队列")
            # print(f"当前线程数已达上限（{self.max_threads}），路径 {path} 加入等待队列")
            self.wait_queue.append((path, item))
            return
        if not os.access(path, os.R_OK):
            logger.error(f"路径 {path} 无权限，无法启动计算")
            self.size_updated.emit(item, self.parent.translation.get("no_permission","无权限"))
            # print(self.parent.translation.get("no_permission","无权限"))
            return
        if not os.access(path, os.W_OK):
            logger.error(f"路径 {path} 无权限，无法启动计算")
            self.size_updated.emit(item, self.parent.translation.get("no_permission","无权限"))
            # print(self.parent.translation.get("no_permission","无权限"))
            return
        # 启动线程并记录
        thread = FolderSizeThread(path)
        self.threads[path] = thread
        thread.size_updated.connect(lambda p, s: self._on_size_updated(p, s, item))
        thread.start()

    def _check_wait_queue(self):
        """检查等待队列并启动新线程"""
        if self.wait_queue and len(self.threads) < self.max_threads:
            path, item = self.wait_queue.pop(0)
            self.start_calculate(path, item)  # 重新触发启动逻辑

    def _on_size_updated(self, path: str, size: str, item: QTreeWidgetItem):
        """线程计算完成后的回调"""
        if size == "unaccessable":
            self.size_updated.emit(item, self.parent.translation.get("unaccessable","无法访问"))
        else:
            self.size_updated.emit(item, size)  # 触发 UI 更新信号
            
        # 直接更新file_list_data中的size字段和raw_size字段
        try:
            # 获取文件列表更新器
            file_list_updater = self.parent.file_list_updater
            
            # 查找并更新file_list_data中的对应项
            for file_info in file_list_updater.file_list_data:
                if file_info.get("path") == path and file_info.get("is_dir"):
                    # 解析格式化大小为字节数
                    size_in_bytes = parse_formatted_size(size)
                    file_info["size"] = size_in_bytes
                    file_info["raw_size"] = size_in_bytes  # 同时更新raw_size字段
                    logger.debug(f"直接更新file_list_data: {path} -> {size_in_bytes} bytes")
                    break
        except Exception as e:
            logger.error(f"直接更新file_list_data失败: {str(e)}")
            
        # 写入数据库（优化异常处理）
        try:
            # ：获取最后修改时间时添加异常捕获
            try:
                from utils.time_utils import get_file_mtime
                last_modified = get_file_mtime(path)
                if last_modified <= 0:
                    raise ValueError("无效时间戳")
                # print(f"路径 {path} 最后修改时间：{last_modified}")
                # a = os.access(path, os.R_OK)
                    #raise PermissionError("无权限访问")
            except Exception as e:
                self.size_updated.emit(item,self.parent.translation.get("error","错误"))
                # print(self.parent.translation.get("error","错误"))
                # print(e)
            self.db.update_cache(
                folder_path=path,
                size=size,
                last_modified=last_modified
            )
            logger.info(f"数据库写入成功，路径：{path}，大小：{size}，最后修改时间：{last_modified}")
        except Exception as e:
            logger.error(f"数据库写入失败，路径：{path}，大小：{size}，错误信息：{str(e)}")
        if path in self.threads:
            del self.threads[path]  # 清理已完成的线程记录
            self._check_wait_queue()  # 新增：清理后立即检查等待队列

    def stop_all_threads(self):
        """停止所有正在运行的线程"""
        thread_count = len(self.threads)
        if thread_count == 0:
            logger.info("无活跃线程需要停止")  # 使用模块日志
            return
        logger.info(f"开始停止 {thread_count} 个文件夹大小计算线程")  # 使用模块日志
        for thread in self.threads.values():
            thread.stop()
            # 等待线程主动退出（最长等待5秒）
            if not thread.wait(5000):  # 5000ms超时
                logger.warning(f"线程 {thread.path} 未及时终止，尝试强制终止")
                thread.terminate()  # 强制终止（最后手段）
                thread.wait(1000)  # 等待强制终止完成
        self.threads.clear()