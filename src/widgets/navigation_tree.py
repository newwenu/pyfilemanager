import os
import sys  # 新增：用于判断操作系统
from PySide6.QtWidgets import QTreeWidgetItem
from PySide6.QtCore import Qt

# Windows 系统保留 win32api 导入，其他系统不导入
if sys.platform == "win32":
    import win32api

def init_navigation_tree(nav_tree, icons):
    """独立的导航树初始化函数"""
    nav_tree.clear()
    
    # 创建"此电脑"根节点
    pc_item = QTreeWidgetItem(nav_tree, ["此电脑"])
    pc_item.setIcon(0, icons.get('hardware', icons['default']))
    pc_item.setData(0, Qt.UserRole, '此电脑')

    # 跨平台获取驱动器/挂载点列表
    if sys.platform == "win32":
        # Windows：使用 win32api 获取逻辑驱动器
        drives = win32api.GetLogicalDriveStrings().split('\x00')[:-1]
    else:
        # Unix-like（macOS/Linux）：获取常见挂载点目录
        if sys.platform == "darwin":  # macOS
            drives = [os.path.join("/Volumes", d) for d in os.listdir("/Volumes") if not d.startswith(".")]
        else:  # Linux
            drives = [os.path.join("/mnt", d) for d in os.listdir("/mnt")] if os.path.exists("/mnt") else []
            # 补充 /media 目录（部分Linux发行版）
            if os.path.exists("/media"):
                drives += [os.path.join("/media", d) for d in os.listdir("/media")]

    for drive in drives:
        try:
            if sys.platform == "win32":
                # Windows：使用 win32api 获取卷标
                vol_info = win32api.GetVolumeInformation(drive)
                drive_label = vol_info[0] or f"本地磁盘 ({drive.strip('\\')})"
            else:
                # Unix-like：直接使用目录名作为显示名称
                drive_label = os.path.basename(drive.rstrip('/'))
            display_name = drive_label
        except Exception as e:
            print(f"获取驱动器信息失败: {drive}, 错误: {str(e)}")
            display_name = f"未知驱动器 ({os.path.basename(drive)})"

        # 创建树项（调整显示文本）
        item = QTreeWidgetItem(nav_tree, [drive.strip('\\')+display_name])
        item.setIcon(0, icons.get('hardware', icons['default']))
        item.setData(0, Qt.UserRole, drive)  # 存储完整路径到 UserRole