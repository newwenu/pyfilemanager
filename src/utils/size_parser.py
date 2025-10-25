"""用于解析格式化大小字符串的工具函数"""

def parse_formatted_size(formatted_size: str) -> int:
    """
    将格式化的大小字符串解析为字节数
    
    Args:
        formatted_size (str): 格式化的大小字符串，如 "1.25MB", "3.50GB" 等
        
    Returns:
        int: 对应的字节数，如果解析失败则返回0
    """
    # 处理特殊状态
    if formatted_size == "unaccessable" or formatted_size == "无法访问":
        return 0
    
    # 定义单位到字节的乘数映射（按长度排序，长的在前，避免匹配到部分单位）
    unit_multipliers = [
        ('TB', 1024 ** 4),
        ('GB', 1024 ** 3),
        ('MB', 1024 ** 2),
        ('KB', 1024),
        ('B', 1)
    ]
    
    # 提取数字和单位
    for unit_suffix, multiplier in unit_multipliers:
        if formatted_size.endswith(unit_suffix):
            try:
                # 提取数字部分
                number_part = formatted_size[:-len(unit_suffix)]
                # 转换为浮点数并计算字节数
                size_value = float(number_part)
                return int(size_value * multiplier)
            except ValueError:
                # 如果转换失败，继续尝试其他单位
                continue
    
    # 如果没有匹配的单位后缀，返回0
    return 0