from PySide6.QtCore import QThread, Signal
from image_manager.get_pic import get_webp
from utils.logging_config import get_logger

logger = get_logger(__name__)

class WebpLoader(QThread):
    loaded = Signal(str)
    
    def run(self):
        try:
            path = get_webp()
            self.loaded.emit(path)
        except Exception as e:
            logger.error(f"web图片加载失败: {e}")
