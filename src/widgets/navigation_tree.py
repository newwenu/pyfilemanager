import os
import sys  # 用于判断操作系统
from PySide6.QtWidgets import QTreeWidgetItem
from PySide6.QtCore import Qt
from utils.logging_config import get_logger
logger = get_logger(__name__)

# Windows 系统保留 win32api 导入，其他系统不导入
if sys.platform == "win32":
    import win32api

def init_navigation_tree(nav_tree, icons, translation: dict):  # 新增 translation 参数
    """独立的导航树初始化函数（适配现有翻译模板）"""
    nav_tree.clear()
    
    # 创建"此电脑"根节点（不变）
    pc_text = translation.get("this_pc", "此电脑")
    pc_item = QTreeWidgetItem(nav_tree, [pc_text])
    pc_item.setIcon(0, icons.get('hardware', icons['default']))
    pc_item.setData(0, Qt.UserRole, '此电脑')

    # 跨平台获取驱动器/挂载点列表（不变）
    if sys.platform == "win32":
        drives = win32api.GetLogicalDriveStrings().split('\x00')[:-1]
    else:
        if sys.platform == "darwin":
            drives = [os.path.join("/Volumes", d) for d in os.listdir("/Volumes") if not d.startswith(".")]
        else:
            drives = [os.path.join("/mnt", d) for d in os.listdir("/mnt")] if os.path.exists("/mnt") else []
            if os.path.exists("/media"):
                drives += [os.path.join("/media", d) for d in os.listdir("/media")]

    for drive in drives:
        try:
            if sys.platform == "win32":
                # Windows：使用翻译替换默认标签
                vol_info = win32api.GetVolumeInformation(drive)
                if vol_info[0]:
                    drive_label = vol_info[0]
                else:
                    # 默认标签使用翻译（如"本地磁盘"）
                    drive_letter = drive.strip('\\')
                    drive_label = translation.get("local_disk_format", "本地磁盘 ({drive_letter})").format(drive_letter=drive_letter)
            else:
                # Unix-like：目录名作为显示名称（无需翻译）
                drive_label = os.path.basename(drive.rstrip('/'))
            display_name = drive_label
        except Exception as e:
            logger.error(f"获取驱动器信息失败: {drive}, 错误: {str(e)}")
            # 关键修改：使用 drive 变量填充翻译模板的 {drive} 占位符
            # 简化驱动器路径显示（Windows 去掉末尾反斜杠，Unix-like 取目录名）
            simplified_drive = drive.strip('\\') if sys.platform == "win32" else os.path.basename(drive.rstrip('/'))
            display_name = translation.get("unknown_drive_format", "未知驱动器 ({drive})").format(drive=simplified_drive)
        
        # 创建树项（不变）
        item = QTreeWidgetItem(nav_tree, [drive.strip('\\')+display_name])
        item.setIcon(0, icons.get('hardware', icons['default']))
        item.setData(0, Qt.UserRole, drive)  # 存储完整路径到 UserRole