import logging
import os
from typing import Optional
from logging.handlers import TimedRotatingFileHandler  # 导入

# 导入配置
try:
    from core import app_config
    HAS_APP_CONFIG = True
except ImportError:
    HAS_APP_CONFIG = False

def init_logging(config_manager: Optional["ConfigManager"] = None):
    """
    统一初始化日志配置（支持定时清理）
    :param config_manager: 配置管理器实例（可选，已弃用，保留参数用于兼容性）
    """
    # 优先使用 app_config，否则使用传入的 config_manager，最后使用默认值
    if HAS_APP_CONFIG:
        # 从 app_config 获取参数
        log_dir = app_config.log_dir
        log_level = app_config.log_level
        rotate_when = app_config.log_rotate_when
        rotate_interval = app_config.log_rotate_interval
        backup_count = app_config.log_backup_count
    elif config_manager:
        # 从 config_manager 获取参数（向后兼容）
        log_dir = config_manager.get("log_dir", "logs")
        log_level = config_manager.get("log_level", "DEBUG").upper()
        rotate_when = config_manager.get("log_rotate_when", "midnight")
        rotate_interval = config_manager.get("log_rotate_interval", 1)
        backup_count = config_manager.get("log_backup_count", 7)
    else:
        # 使用默认值
        log_dir = "logs"
        log_level = "DEBUG"
        rotate_when = "midnight"
        rotate_interval = 1
        backup_count = 7
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)

    # 配置基础日志（显式设置处理器级别为DEBUG）
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, "app.log"),
        when=rotate_when,
        interval=rotate_interval,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # 显式设置文件处理器级别

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # 显式设置控制台处理器级别

    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        datefmt=date_format,
        handlers=[file_handler, console_handler]  # 使用显式配置的处理器
    )

def get_logger(name: str) -> logging.Logger:
    """统一获取日志记录器（确保使用全局配置）"""
    return logging.getLogger(name)
