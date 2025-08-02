import logging
import os
from typing import Optional
from logging.handlers import TimedRotatingFileHandler  # 导入

from config_manager.config_manager import ConfigManager

def init_logging(config_manager: Optional["ConfigManager"] = None):
    """
    统一初始化日志配置（支持定时清理）
    :param config_manager: 配置管理器实例（可选）
    """
    # 从配置获取参数（无配置时使用默认值，调整默认日志级别为DEBUG）
    log_dir = config_manager.get("log_dir", "logs") if config_manager else "logs"
    log_level = config_manager.get("log_level", "DEBUG").upper() if config_manager else "DEBUG"  # 默认DEBUG级别
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 从配置获取日志轮换策略（默认每天轮换，保留7天）
    rotate_when = config_manager.get("log_rotate_when", "midnight")
    rotate_interval = config_manager.get("log_rotate_interval", 1)
    backup_count = config_manager.get("log_backup_count", 7)

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
