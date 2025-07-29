import os
import sys  # 新增：用于判断操作系统
# 原有的 win32api/win32con 导入保留，但增加条件判断
if sys.platform == "win32":
    import win32api
    import win32con

from PySide6.QtGui import QImage, QPainter, QFont, QPixmap, QIcon
from PySide6.QtCore import Qt
from PySide6.QtCore import QRect

# ：导入配置管理器
from config_manager.config_manager import ConfigManager


# 初始化配置管理器（使用默认路径或自定义路径）
config_manager = ConfigManager(os.path.join("userdata","file-icon_type","file-icon_type.json"))

# 从配置中加载文件类型映射（优化：构建扩展名反向字典）
_original_type_map = {k: tuple(v) for k, v in config_manager.get(
    "file_type_mapping",
    {
        'text': ('.txt', '.md', '.rtf', '.odt'),
        'document': ('.doc', '.docx',),  
        'spreadsheet': ('.xls', '.xlsx'), 
        'image': ('.jpg', '.png', '.gif', '.jpeg', '.bmp', '.webp', '.svg'),
        'video': ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'),
        'music': ('.mp3', '.wav', '.flac', '.aac', '.ogg'),
        'pdf': ('.pdf',),
        'archive': ('.zip', '.rar', '.7z', '.tar', '.gz'),
        'exe': ('.exe', '.msi', '.bat', '.cmd'),
        'shortcut': ('.lnk',),
        'code': ('.py', '.js', '.html', '.css', '.json', '.xml','.cpp','.c')
    }
).items()}

# 构建扩展名到类型的反向字典（优化核心）
EXT_TO_TYPE = {}
for file_type, exts in _original_type_map.items():
    for ext in exts:
        EXT_TO_TYPE[ext.lower()] = file_type  # 统一小写处理扩展名

def get_file_type(filename):
    """优化后的文件类型判断（O(1)时间复杂度）"""
    ext = os.path.splitext(filename)[1].lower()
    return EXT_TO_TYPE.get(ext, 'default')  # 直接通过字典查找

def format_size(size):
    """格式化文件大小"""
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    while size >= 1024 and unit_index < 4:
        size /= 1024
        unit_index += 1
    return f'{size:.2f}{units[unit_index]}'

def create_char_icon(char):
    """生成字符图标"""
    size = 32
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    try:
        font = QFont("Segoe UI Emoji", 24)
    except:
        font = QFont()
    painter.setFont(font)
    painter.setRenderHint(QPainter.TextAntialiasing)
    text_rect = painter.boundingRect(QRect(0, 0, size, size), Qt.AlignCenter, char)
    x = (size - text_rect.width()) // 2
    y = (size - text_rect.height()) // 2 + text_rect.height() - 10
    painter.drawText(x, y, char)
    painter.end()
    return QIcon(QPixmap.fromImage(image))

def should_show(entry, show_hidden):
    """判断是否显示文件"""
    if show_hidden:
        return True
    try:
        if sys.platform == "win32":
            # Windows：使用 win32api 检测隐藏属性
            is_hidden = win32api.GetFileAttributes(entry.path) & win32con.FILE_ATTRIBUTE_HIDDEN
        else:
            # Unix-like（macOS/Linux）：检测文件名是否以 . 开头
            is_hidden = entry.name.startswith('.')
        return not (entry.name.startswith('.') or is_hidden)  # 保留原逻辑中的 . 开头判断（兼容所有平台）
    except:
        return False

def get_icon_char(file_type):
    """为未找到媒体图标的类型生成字符图标（备用方案）"""
    char_map = {
        'folder': '📂',
        'text': '📄',
        'image': '🖼️',
        'video': '🎥',
        'music': '🎵',
        'pdf': '📑',
        'archive': '📦',
        'exe': '🚀',
        'code': '🛠️',
        'hardware': '💾',
        'document': '📄',
        'spreadsheet': '📊',
        'font': '🔤',
        'database': '🗄️', 
        'shortcut': '🔗',
        'config': '⚙️',
        'default': '📄'
    }
    return char_map.get(file_type, '?')
