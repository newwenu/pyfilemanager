from pathlib import Path
from PySide6.QtGui import QIcon
from utils.file_utils import get_icon_char, create_char_icon

def create_icon_set(icon_dir: str = "media") -> tuple[dict, dict]:
    """创建图标集合，自动处理缺失图标回退到字符图标"""
    icon_dir_path = Path(icon_dir)
    icon_dir_path.mkdir(exist_ok=True)
    
    icon_mapping = {
        'folder': 'folder.png',
        'text': 'text.png',
        'image': 'image.png',
        'video': 'video.png',
        'music': 'music.png',
        'pdf': 'pdf.png',
        'archive': 'archive.png',
        'exe': 'exe.png',
        'code': 'code.png',
        'hardware': 'hardware.png',
        'document': 'document.png',
        'spreadsheet': 'spreadsheet.png', 
        'default': 'file.png'
    }
    
    icons = {}
    icon_paths = {}
    for file_type, filename in icon_mapping.items():
        icon_path = icon_dir_path / filename
        icon_paths[file_type] = str(icon_path)
        
        if icon_path.exists():
            icons[file_type] = QIcon(str(icon_path))
        else:
            # 使用字符图标作为回退
            icons[file_type] = create_char_icon(get_icon_char(file_type))
    
    return icons, icon_paths

