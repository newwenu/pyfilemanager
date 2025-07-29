import sys
import os
from typing import List

def get_system_drives() -> List[str]:
    """
    跨平台获取系统驱动器/挂载点列表（Windows/macOS/Linux）
    :return: 驱动器路径列表（如 ["C:\\", "/Volumes/MyDisk"]）
    """
    if sys.platform == "win32":
        import win32api
        return win32api.GetLogicalDriveStrings().split('\x00')[:-1]
    else:
        mount_points = []
        if sys.platform == "darwin":  # macOS
            mount_points = [
                os.path.join("/Volumes", d) 
                for d in os.listdir("/Volumes") 
                if not d.startswith(".")  # 过滤隐藏卷（如 ".Trash"）
            ]
        else:  # Linux
            for base in ["/mnt", "/media"]:
                if os.path.exists(base):
                    mount_points.extend([
                        os.path.join(base, d) 
                        for d in os.listdir(base)
                    ])
        # return list(set(mount_points))  # 去重
            # 去重后添加用户主目录（Linux/macOS）
            drives = list(set(mount_points))
            # 新增：获取用户主目录（如 "/home/user" 或 "/Users/user"）
            home_dir = os.path.expanduser('~')
            if home_dir not in drives:  # 避免重复
                drives.append(home_dir)
        return drives

def get_simplified_drive_display(drive: str, translation: dict) -> str:
    """
    统一获取简化的驱动器显示名称（跨平台 + 翻译支持）
    :param drive: 驱动器完整路径（如 "C:\\" 或 "/Volumes/MyDisk"）
    :param translation: 翻译字典
    :return: 格式化后的显示名称（如 "未知驱动器 (C)" 或 "未知驱动器 (MyDisk)"）
    """
    # 跨平台路径简化
    if sys.platform == "win32":
        simplified = drive.strip('\\')  # Windows: 去掉末尾反斜杠（如 "C:\\" → "C"）
    else:
        simplified = os.path.basename(drive.rstrip('/'))  # Unix-like: 取目录名（如 "/Volumes/MyDisk" → "MyDisk"）
    
    # 使用翻译模板格式化
    return translation.get("unknown_drive_format", "未知驱动器 ({drive})").format(drive=simplified)
