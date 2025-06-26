from PySide6.QtWidgets import QTreeWidgetItem, QProgressBar
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
import sys
from utils.file_utils import format_size  # 确保路径正确
class DriveListManager:
    @classmethod
    def update_drive_list(cls, file_list, config, icons, status_bar, current_path):
        """独立管理驱动器列表的创建逻辑"""
        file_list.clear()
        file_list.setUniformRowHeights(False)  # 保持行高独立
        
        # 1. 基础配置读取
        # drives = win32api.GetLogicalDriveStrings().split('\x00')[:-1]
        if sys.platform == "win32":
            import win32api
            # Windows：使用 win32api 获取逻辑驱动器
            drives = win32api.GetLogicalDriveStrings().split('\x00')[:-1]
        else:
            # Unix-like（macOS/Linux）：获取常见挂载点目录
            mount_points = []
            if sys.platform == "darwin":  # macOS
                mount_points = [os.path.join("/Volumes", d) for d in os.listdir("/Volumes") if not d.startswith(".")]
            else:  # Linux
                for base in ["/mnt", "/media"]:
                    if os.path.exists(base):
                        mount_points.extend([os.path.join(base, d) for d in os.listdir(base)])
            drives = list(set(mount_points))  # 去重

        file_list.setHeaderLabels(["名称", "空间使用情况"])
        
        # 2. 样式配置（从config读取）
        drive_icon_size = config.get("drive_icon_size", 48)
        drive_font_size = config.get("Drive_font_size", 20)
        file_list.setIconSize(QSize(drive_icon_size, drive_icon_size))  # 图标尺寸
        
        # 3. 字体与行高设置
        larger_font = QFont()
        larger_font.setPointSize(drive_font_size)
        new_height = drive_icon_size + 10  # 行高计算
        
        # 4. 遍历磁盘创建条目
        for drive in drives:
            # 磁盘信息获取（保持原有逻辑）
            try:
                if sys.platform == "win32":
                    # Windows：使用 win32api 获取卷标和空间
                    free_bytes, total_bytes = win32api.GetDiskFreeSpaceEx(drive)[:2]
                    vol_info = win32api.GetVolumeInformation(drive)
                    display_name = f"{vol_info[0]} ({drive.strip('\\')})" if vol_info[0] else f"本地磁盘 ({drive.strip('\\')})"
                else:
                    # Unix-like：使用 shutil 跨平台获取空间，目录名作为卷标
                    total_bytes, used_bytes, free_bytes = shutil.disk_usage(drive)
                    display_name = os.path.basename(drive.rstrip('/'))  # 目录名作为显示名称
                
                drive_letter = drive.strip('\\')
                free_bytes, total_bytes = win32api.GetDiskFreeSpaceEx(drive)[:2]
                used_bytes = total_bytes - free_bytes
                percent_used = (used_bytes / total_bytes * 100) if total_bytes > 0 else 0
                total_str = format_size(total_bytes)
                used_str = format_size(used_bytes)
                # vol_info = win32api.GetVolumeInformation(drive)
                # display_name = f"{vol_info[0]} ({drive_letter})" if vol_info[0] else f"本地磁盘 ({drive_letter})"
            except:
                display_name = f"未知驱动器 ({drive.strip('\\')})"
                used_str = total_str = "容量未知"
                percent_used = 0
            
            # 创建列表项
            item = QTreeWidgetItem(file_list, [display_name])
            item.setFont(0, larger_font)
            item.setIcon(0, icons.get('hardware', icons['default']))
            item.setSizeHint(0, QSize(0, new_height))
            item.setSizeHint(1, QSize(0, new_height))
            item.setData(0, Qt.UserRole, drive)
            
            # 进度条创建（保持原有逻辑）
            progress = QProgressBar()
            progress.setRange(0, 1000)
            progress.setValue(percent_used * 10)
            progress.setFormat(f"{used_str} / {total_str} ({percent_used:.1f}%)")
            progress.setAlignment(Qt.AlignCenter)
            progress.setStyleSheet("""
                QProgressBar { border: 1px solid #444; border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #6699ff; border-radius: 5px; }
            """)
            file_list.setItemWidget(item, 1, progress)
        
        # 5. 列宽调整与状态栏更新
        file_list.setColumnWidth(0, 180)
        file_list.setColumnWidth(1, 300)
        status_bar.showMessage(f"{current_path} | 磁盘总数：{len(drives)}")
