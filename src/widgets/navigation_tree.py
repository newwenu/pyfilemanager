import win32api
from PySide6.QtWidgets import QTreeWidgetItem
from PySide6.QtCore import Qt

def init_navigation_tree(nav_tree, icons):
    """独立的导航树初始化函数"""
    nav_tree.clear()
    
    # 创建"此电脑"根节点
    pc_item = QTreeWidgetItem(nav_tree, ["此电脑"])
    pc_item.setIcon(0, icons.get('hardware', icons['default']))
    pc_item.setData(0, Qt.UserRole, '此电脑')

    # 遍历系统驱动器
    drives = win32api.GetLogicalDriveStrings().split('\x00')[:-1]
    for drive in drives:
        try:
            # 获取驱动器卷标信息（带异常处理）
            vol_info = win32api.GetVolumeInformation(drive)
            drive_label = vol_info[0]  # 卷标（可能为空）
            display_name = drive_label if drive_label else f"本地磁盘 ({drive.strip('\\')})"
        except Exception as e:
            print(f"获取驱动器信息失败: {drive}, 错误: {str(e)}")
            display_name = f"未知驱动器 ({drive.strip('\\')})"  # 异常时显示默认格式
        
        drive_letter = drive.strip('\\')  # 提取驱动器字母
        # 创建树项并设置图标和文本
        item = QTreeWidgetItem(nav_tree, [f"{drive_letter}{display_name}"])
        item.setIcon(0, icons.get('hardware', icons['default']))  # 使用硬件图标
        item.setData(0, Qt.UserRole, drive)  # 存储完整路径到UserRole
