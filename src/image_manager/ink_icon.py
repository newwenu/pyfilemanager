from PySide6.QtWidgets import QFileIconProvider
from PySide6.QtCore import QFileInfo

def get_file_icon(file_path, icon_size=None):
    """
    获取文件图标
    :param file_path: 文件路径
    :param icon_size: 图标大小
    :return: QPixmap对象或None
    """
    provider = QFileIconProvider()
    file_info = QFileInfo(file_path)
    icon = provider.icon(file_info)
    
    if icon.isNull():
        return None
    
    # 获取合适的图标大小
    if icon_size:
        pixmap = icon.pixmap(icon_size, icon_size)
    else:
        # 使用最大可用尺寸
        sizes = icon.availableSizes()
        if not sizes:
            return None
        max_size = max(sizes, key=lambda s: s.width() * s.height())
        pixmap = icon.pixmap(max_size)
    
    return pixmap

def get_shortcut_icon_pixmap(shortcut_path, icon_size=None):
    """
    获取文件图标并返回QPixmap对象
    :param shortcut_path: 文件路径
    :param icon_size: 图标大小
    :return: QPixmap对象或None
    """
    
    pixmap = get_file_icon(shortcut_path, icon_size)
    
    if pixmap:
        return pixmap
    return None