import os
import win32api
import win32con
from datetime import datetime
from PySide6.QtGui import QImage, QPainter, QFont, QColor, QPixmap, QIcon
from PySide6.QtCore import Qt
from PySide6.QtCore import QRect

def get_file_type(filename):
    """优化后的文件类型判断"""
    ext = os.path.splitext(filename)[1].lower()
    
    # 使用字典映射扩展名到文件类型
    type_map = {
        'text': ('.txt', '.md', '.rtf', '.odt'),
        'document': ('.doc', '.docx'),  
        'spreadsheet': ('.xls', '.xlsx'), 
        'image': ('.jpg', '.png', '.gif', '.jpeg', '.bmp', '.webp', '.svg'),
        'video': ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'),
        'music': ('.mp3', '.wav', '.flac', '.aac', '.ogg'),
        'pdf': ('.pdf'),
        'archive': ('.zip', '.rar', '.7z', '.tar', '.gz'),
        'exe': ('.exe', '.msi', '.bat', '.cmd'),
        'shortcut': ('.lnk',),
        'code': ('.py', '.js', '.html', '.css', '.json', '.xml','.cpp','.c')
    }
    
    for file_type, exts in type_map.items():
        if ext in exts:
            return file_type
    return 'default'

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
        is_hidden = win32api.GetFileAttributes(entry.path) & win32con.FILE_ATTRIBUTE_HIDDEN
        return not (entry.name.startswith('.') or is_hidden)
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
        'exe': '⚙️',
        'code': '🛠️',
        'hardware': '💾',
        'document': '📄',
        'spreadsheet': '📊',
        'font': '🔤',
        'database': '🗄️', 
        'shortcut': '🔗',
        'default': '📄'
    }
    return char_map.get(file_type, '?')