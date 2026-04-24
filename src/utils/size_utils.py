"""
文件大小处理工具模块

提供文件大小的格式化、解析、比较等统一接口
"""

import math
from typing import Union, Tuple

# 预定义的单位常量
_SIZE_UNITS = ('B', 'KB', 'MB', 'GB', 'TB', 'PB')
_SIZE_THRESHOLDS = tuple(1024 ** i for i in range(6))
_UNIT_MULTIPLIERS = {
    'B': 1,
    'KB': 1024,
    'MB': 1024 ** 2,
    'GB': 1024 ** 3,
    'TB': 1024 ** 4,
    'PB': 1024 ** 5,
}


def format_size(size: Union[int, float], precision: int = 2) -> str:
    """
    将字节数格式化为人类可读的大小字符串

    Args:
        size: 文件大小（字节）
        precision: 小数位数（默认2位）

    Returns:
        格式化后的大小字符串，如 "1.25MB"

    Examples:
        >>> format_size(1024)
        '1.00KB'
        >>> format_size(1536)
        '1.50KB'
        >>> format_size(0)
        '0B'
    """
    if size < 0:
        raise ValueError(f"大小不能为负数: {size}")

    if size == 0:
        return "0B"

    # 使用对数快速确定单位索引
    unit_index = min(int(math.log2(size) / 10), len(_SIZE_UNITS) - 1)

    # 计算格式化后的大小值
    size_value = size / (1024 ** unit_index)

    # 格式化输出
    unit = _SIZE_UNITS[unit_index]
    return f"{size_value:.{precision}f}{unit}"


def format_size_auto_precision(size: Union[int, float]) -> str:
    """
    智能格式化大小，根据数值自动选择小数位数

    - 大于等于 100 的数值：不显示小数
    - 10-100 之间的数值：显示1位小数
    - 小于 10 的数值：显示2位小数

    Args:
        size: 文件大小（字节）

    Returns:
        格式化后的大小字符串

    Examples:
        >>> format_size_auto_precision(1024 * 1024 * 100)
        '100MB'
        >>> format_size_auto_precision(1024 * 15)
        '15.0KB'
    """
    if size == 0:
        return "0B"

    unit_index = min(int(math.log2(size) / 10), len(_SIZE_UNITS) - 1)
    size_value = size / (1024 ** unit_index)

    # 根据数值大小自动选择精度
    if size_value >= 100:
        precision = 0
    elif size_value >= 10:
        precision = 1
    else:
        precision = 2

    unit = _SIZE_UNITS[unit_index]
    return f"{size_value:.{precision}f}{unit}"


def parse_size(size_str: str) -> int:
    """
    将格式化的大小字符串解析为字节数

    Args:
        size_str: 格式化的大小字符串，如 "1.25MB", "3.50GB"
                  支持的大小写不敏感，如 "1.25mb", "1.25MB"

    Returns:
        对应的字节数，如果解析失败则返回 0

    Examples:
        >>> parse_size("1.25MB")
        1310720
        >>> parse_size("1024KB")
        1048576
        >>> parse_size("无法访问")
        0
    """
    if not size_str or not isinstance(size_str, str):
        return 0

    # 处理特殊状态字符串
    special_states = ('unaccessable', '无法访问', 'calculating', '计算中',
                      'no_permission', '无权限', 'error', '错误')
    if size_str.lower() in special_states or size_str in special_states:
        return 0

    # 去除空白并统一大写
    size_str = size_str.strip().upper()

    # 尝试解析数字和单位
    for unit, multiplier in _UNIT_MULTIPLIERS.items():
        if size_str.endswith(unit):
            try:
                number_part = size_str[:-len(unit)]
                size_value = float(number_part)
                return int(size_value * multiplier)
            except ValueError:
                continue

    # 如果没有匹配的单位后缀，尝试直接解析为数字（假设为字节）
    try:
        return int(float(size_str))
    except ValueError:
        return 0


def parse_size_strict(size_str: str) -> Tuple[int, str]:
    """
    严格解析大小字符串，返回字节数和单位

    Args:
        size_str: 格式化的大小字符串

    Returns:
        (字节数, 单位) 的元组，解析失败返回 (0, '')

    Examples:
        >>> parse_size_strict("1.25MB")
        (1310720, 'MB')
    """
    if not size_str or not isinstance(size_str, str):
        return 0, ''

    size_str = size_str.strip().upper()

    for unit, multiplier in _UNIT_MULTIPLIERS.items():
        if size_str.endswith(unit):
            try:
                number_part = size_str[:-len(unit)]
                size_value = float(number_part)
                return int(size_value * multiplier), unit
            except ValueError:
                continue

    return 0, ''


def compare_sizes(size1: Union[int, str], size2: Union[int, str]) -> int:
    """
    比较两个大小

    Args:
        size1: 第一个大小（字节数或格式化字符串）
        size2: 第二个大小（字节数或格式化字符串）

    Returns:
        -1: size1 < size2
         0: size1 == size2
         1: size1 > size2

    Examples:
        >>> compare_sizes("1MB", "1024KB")
        0
        >>> compare_sizes(1024, "1KB")
        0
    """
    # 统一转换为字节数
    bytes1 = size1 if isinstance(size1, int) else parse_size(size1)
    bytes2 = size2 if isinstance(size2, int) else parse_size(size2)

    if bytes1 < bytes2:
        return -1
    elif bytes1 > bytes2:
        return 1
    else:
        return 0


def get_size_unit(size: Union[int, float]) -> str:
    """
    获取大小对应的单位

    Args:
        size: 文件大小（字节）

    Returns:
        单位字符串（B, KB, MB, GB, TB, PB）

    Examples:
        >>> get_size_unit(1024)
        'KB'
        >>> get_size_unit(1024 ** 3)
        'GB'
    """
    if size <= 0:
        return 'B'
    unit_index = min(int(math.log2(size) / 10), len(_SIZE_UNITS) - 1)
    return _SIZE_UNITS[unit_index]


def convert_size(size: Union[int, float], target_unit: str) -> float:
    """
    将大小转换为目标单位

    Args:
        size: 文件大小（字节）
        target_unit: 目标单位（B, KB, MB, GB, TB, PB）

    Returns:
        转换后的大小值

    Examples:
        >>> convert_size(1024 * 1024, 'KB')
        1024.0
        >>> convert_size(1024 * 1024, 'MB')
        1.0
    """
    target_unit = target_unit.upper()
    if target_unit not in _UNIT_MULTIPLIERS:
        raise ValueError(f"未知的单位: {target_unit}")

    return size / _UNIT_MULTIPLIERS[target_unit]


def is_valid_size_string(size_str: str) -> bool:
    """
    检查字符串是否为有效的大小格式

    Args:
        size_str: 待检查的字符串

    Returns:
        是否为有效的大小格式

    Examples:
        >>> is_valid_size_string("1.25MB")
        True
        >>> is_valid_size_string("invalid")
        False
    """
    if not size_str or not isinstance(size_str, str):
        return False

    # 处理特殊状态
    special_states = ('unaccessable', '无法访问', 'calculating', '计算中',
                      'no_permission', '无权限', 'error', '错误')
    if size_str.lower() in special_states or size_str in special_states:
        return True

    size_str = size_str.strip().upper()

    for unit in _UNIT_MULTIPLIERS.keys():
        if size_str.endswith(unit):
            try:
                number_part = size_str[:-len(unit)]
                float(number_part)
                return True
            except ValueError:
                return False

    # 尝试直接解析为数字
    try:
        float(size_str)
        return True
    except ValueError:
        return False


# 向后兼容的别名
format_file_size = format_size
parse_formatted_size = parse_size
