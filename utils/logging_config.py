import logging
import os
from typing import Optional
from logging.handlers import TimedRotatingFileHandler  # 新增导入

from utils.config_manager import ConfigManager

def init_logging(config_manager: Optional["ConfigManager"] = None):
    """
    统一初始化日志配置（支持定时清理）
    :param config_manager: 配置管理器实例（可选）
    """
    # 从配置获取参数（无配置时使用默认值）
    log_dir = config_manager.get("log_dir", "logs") if config_manager else "logs"
    log_level = config_manager.get("log_level", "INFO").upper() if config_manager else "INFO"
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 新增：从配置获取日志轮换策略（默认每天轮换，保留7天）
    rotate_when = config_manager.get("log_rotate_when", "midnight")  # 轮换时间点（midnight=每天0点）
    rotate_interval = config_manager.get("log_rotate_interval", 1)  # 轮换间隔（天）
    backup_count = config_manager.get("log_backup_count", 7)  # 保留最近7天的日志

    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)

    # 配置基础日志（替换原FileHandler为TimedRotatingFileHandler）
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        datefmt=date_format,
        handlers=[
            TimedRotatingFileHandler(
                filename=os.path.join(log_dir, "app.log"),
                when=rotate_when,  # 按天轮换
                interval=rotate_interval,
                backupCount=backup_count,  # 保留7个旧文件（自动删除更早的）
                encoding="utf-8"
            ),
            logging.StreamHandler()  # 控制台输出保持不变
        ]
    )

def get_logger(name: str) -> logging.Logger:
    """统一获取日志记录器（确保使用全局配置）"""
    return logging.getLogger(name)
