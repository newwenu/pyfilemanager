from pathlib import Path
from PySide6.QtGui import QIcon,QPixmap
from PySide6.QtCore import QSize,Qt
from utils.file_utils import get_icon_char, create_char_icon

# 独立图标类型映射（便于后续维护）
ICON_TYPE_MAPPING = {
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

def create_icon_set(icon_dir: str = "media", icon_size: int = 32) -> tuple[dict, dict]:
    """创建图标集合，自动处理缺失图标回退到字符图标（优化版）"""
    # 转换为绝对路径（避免相对路径问题）
    icon_dir_path = Path(icon_dir).resolve()
    icon_dir_path.mkdir(exist_ok=True)
    
    icons = {}
    icon_paths = {}
    char_icon_cache = {}  # 新增：字符图标缓存
    target_size = QSize(icon_size, icon_size)  # 从参数获取目标尺寸
    for file_type, filename in ICON_TYPE_MAPPING.items():
        icon_path = icon_dir_path / filename
        icon_paths[file_type] = str(icon_path)
        
        if icon_path.exists():
            # 加载并缩放图标（关键修改）
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    target_size,
                    Qt.AspectRatioMode.KeepAspectRatio,  # 保持宽高比
                    Qt.TransformationMode.SmoothTransformation  # 平滑缩放
                )
                icons[file_type] = QIcon(scaled_pixmap)
            # icons[file_type] = QIcon(str(icon_path))
        else:
            # 记录缺失图标警告
            # logging.warning(f"图标文件缺失: {icon_path}，将使用字符图标替代")
            
            # 使用缓存避免重复生成字符图标
            char = get_icon_char(file_type)
            if char not in char_icon_cache:
                char_icon_cache[char] = create_char_icon(char)
            icons[file_type] = char_icon_cache[char]
    
    return icons, icon_paths

