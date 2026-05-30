import logging
import os
import sys
import functools
import time
from typing import Optional, Dict, Any
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# 导入配置
try:
    from core import app_config
    HAS_APP_CONFIG = True
except ImportError:
    HAS_APP_CONFIG = False

# 模块到日志文件的映射
MODULE_LOG_MAPPING = {
    'core': 'core.log',
    'widgets': 'ui.log',
    'threads': 'threads.log',
    'dbload_manager': 'database.log',
    'handlers': 'handlers.log',
    'image_manager': 'image.log',
    'file_operator': 'file_ops.log',
}


def _get_module_log_file(logger_name: str) -> str:
    """根据logger名称获取对应的日志文件"""
    for module, log_file in MODULE_LOG_MAPPING.items():
        if logger_name.startswith(module) or module in logger_name:
            return log_file
    return 'app.log'


def init_logging(config_manager: Optional[Any] = None):
    """
    统一初始化日志配置（支持定时清理和多文件分离）
    :param config_manager: 配置管理器实例（可选）
    """
    # 优先使用传入的 config_manager（确保能读取到配置文件中的值）
    # 否则使用 app_config，最后使用默认值
    if config_manager:
        log_dir = getattr(config_manager, 'get', lambda k, d: d)("log_dir", "logs")
        log_level = getattr(config_manager, 'get', lambda k, d: d)("log_level", "DEBUG").upper()
        rotate_when = getattr(config_manager, 'get', lambda k, d: d)("log_rotate_when", "midnight")
        rotate_interval = getattr(config_manager, 'get', lambda k, d: d)("log_rotate_interval", 1)
        backup_count = getattr(config_manager, 'get', lambda k, d: d)("log_backup_count", 7)
    elif HAS_APP_CONFIG:
        log_dir = app_config.log_dir
        log_level = app_config.log_level
        rotate_when = app_config.log_rotate_when
        rotate_interval = app_config.log_rotate_interval
        backup_count = app_config.log_backup_count
    else:
        log_dir = "logs"
        log_level = "DEBUG"
        rotate_when = "midnight"
        rotate_interval = 1
        backup_count = 7
    
    # 增强的日志格式
    log_format = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(threadName)-12s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)

    # 清除现有的处理器（避免重复）
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 设置根日志级别
    root_logger.setLevel(getattr(logging, log_level))

    # 创建控制台处理器（INFO级别，生产环境更清爽）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(levelname)s | %(name)s | %(message)s",
        datefmt=date_format
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 创建主文件处理器（所有日志）
    main_file_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, "app.log"),
        when=rotate_when,
        interval=rotate_interval,
        backupCount=backup_count,
        encoding="utf-8"
    )
    main_file_handler.setLevel(logging.DEBUG)
    main_formatter = logging.Formatter(log_format, datefmt=date_format)
    main_file_handler.setFormatter(main_formatter)
    root_logger.addHandler(main_file_handler)

    # 为各模块创建单独的日志文件
    for module, log_file in MODULE_LOG_MAPPING.items():
        module_handler = TimedRotatingFileHandler(
            filename=os.path.join(log_dir, log_file),
            when=rotate_when,
            interval=rotate_interval,
            backupCount=backup_count,
            encoding="utf-8"
        )
        module_handler.setLevel(logging.DEBUG)
        module_handler.setFormatter(main_formatter)
        
        # 使用过滤器只记录对应模块的日志
        module_filter = logging.Filter()
        module_filter.filter = lambda record, mod=module: record.name.startswith(mod) or mod in record.name
        module_handler.addFilter(module_filter)
        root_logger.addHandler(module_handler)

    # 记录日志系统初始化完成
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统初始化完成 | 级别: {log_level} | 目录: {os.path.abspath(log_dir)}")


def get_logger(name: str) -> logging.Logger:
    """统一获取日志记录器（确保使用全局配置）"""
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, msg: str, exception: Exception):
    """
    记录异常信息（包含完整堆栈）
    
    使用示例:
        try:
            risky_operation()
        except Exception as e:
            log_exception(logger, "操作失败", e)
    """
    logger.error(f"{msg}: {exception}", exc_info=True)


def log_performance(logger: Optional[logging.Logger] = None, operation_name: str = ""):
    """
    性能日志装饰器 - 记录函数执行时间
    
    使用示例:
        @log_performance(logger, "加载文件列表")
        def load_file_list(self, path):
            # ... 耗时操作
            pass
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                
                # 根据耗时选择日志级别
                if elapsed > 1.0:
                    logger.warning(f"{operation_name or func.__name__} 完成，耗时较长: {elapsed:.3f}s")
                else:
                    logger.debug(f"{operation_name or func.__name__} 完成，耗时: {elapsed:.3f}s")
                
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                logger.error(f"{operation_name or func.__name__} 失败，耗时: {elapsed:.3f}s, 错误: {e}", exc_info=True)
                raise
        return wrapper
    return decorator


def update_log_level(level: str):
    """
    动态更新日志级别（支持热更新）
    
    使用示例:
        update_log_level("DEBUG")  # 切换到调试模式
        update_log_level("INFO")   # 切换到信息模式
    """
    root_logger = logging.getLogger()
    new_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(new_level)
    
    # 更新所有处理器的级别
    for handler in root_logger.handlers:
        if isinstance(handler, TimedRotatingFileHandler):
            handler.setLevel(logging.DEBUG)  # 文件始终记录DEBUG
        else:
            handler.setLevel(new_level)
    
    logger = logging.getLogger(__name__)
    logger.info(f"日志级别已动态更新为: {level.upper()}")


def get_log_stats(log_dir: str = "logs") -> Dict[str, Any]:
    """
    获取日志统计信息
    
    返回:
        {
            'total_size_mb': 总大小(MB),
            'file_count': 日志文件数量,
            'files': [{'name': 文件名, 'size_mb': 大小(MB)}, ...]
        }
    """
    stats = {
        'total_size_mb': 0,
        'file_count': 0,
        'files': []
    }
    
    if not os.path.exists(log_dir):
        return stats
    
    for filename in os.listdir(log_dir):
        if filename.endswith('.log'):
            filepath = os.path.join(log_dir, filename)
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            stats['files'].append({
                'name': filename,
                'size_mb': round(size_mb, 2)
            })
            stats['total_size_mb'] += size_mb
            stats['file_count'] += 1
    
    stats['total_size_mb'] = round(stats['total_size_mb'], 2)
    return stats


class LogContext:
    """
    日志上下文管理器 - 用于记录代码块执行时间
    
    使用示例:
        with LogContext(logger, "批量重命名"):
            for file in files:
                rename(file)
    """
    
    def __init__(self, logger: logging.Logger, operation: str, log_level: str = "debug"):
        self.logger = logger
        self.operation = operation
        self.log_level = getattr(logging, log_level.upper())
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        self.logger.log(self.log_level, f"开始: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        if exc_type is None:
            self.logger.log(self.log_level, f"完成: {self.operation}，耗时: {elapsed:.3f}s")
        else:
            self.logger.error(f"失败: {self.operation}，耗时: {elapsed:.3f}s, 错误: {exc_val}")
        return False  # 不抑制异常
