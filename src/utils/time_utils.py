import os
import time
from datetime import datetime

def get_file_mtime(file_path):
    """
    自定义获取文件修改时间的方法
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        float: 文件修改时间的时间戳，如果出错则返回0
    """
    try:
        # 使用os.path.getmtime获取文件修改时间
        mtime = os.path.getmtime(file_path)
        # 确保时间戳有效
        if mtime > 0:
            return mtime
        else:
            return 0
    except (OSError, ValueError, Exception) as e:
        # 处理各种可能的异常情况
        # print(f"获取文件修改时间失败: {file_path}, 错误: {str(e)}")
        return 0

def format_mtime_timestamp(timestamp):
    """
    格式化时间戳为可读的日期时间格式
    
    Args:
        timestamp (float): 时间戳
        
    Returns:
        str: 格式化后的时间字符串，格式为 "YYYY-MM-DD HH:MM"
    """
    if timestamp and timestamp > 0:
        try:
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
        except (ValueError, OSError, Exception):
            return ""
    return ""

def format_mtime_timestamp_full(timestamp):
    """
    格式化时间戳为完整的日期时间格式
    
    Args:
        timestamp (float): 时间戳
        
    Returns:
        str: 格式化后的时间字符串，格式为 "YYYY-MM-DD HH:MM:SS"
    """
    if timestamp and timestamp > 0:
        try:
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError, Exception):
            return ""
    return ""