from widgets.drive_list_manager import DriveListManager

def show_drives_in_filelist(self, config):
    """驱动器列表入口函数（仅负责调用管理类）"""
    DriveListManager.update_drive_list(
        file_list=self.file_list,
        config=config,
        icons=self.icons,
        status_bar=self.status_bar,
        current_path=self.current_path
    )
