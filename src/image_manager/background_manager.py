import os
from PySide6.QtGui import QImage, QPixmap, Qt
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QLabel
from utils.logging_config import get_logger
logger = get_logger(__name__)
class BackgroundManager:
    def __init__(self, bg_label: QLabel, image_path: str):
        self.bg_label = bg_label  # 背景标签控件
        self.image_path = image_path  # 背景图片路径
        self.original_image = QImage()  # 缓存原始图片
        self.cached_size = QSize()  # 新增：缓存最后一次渲染的尺寸
        self.cached_pixmap = QPixmap()  # 新增：缓存渲染后的图片

    def load_background(self):
        """加载并初始化背景图片（优化版：含尺寸缓存）"""
        if not os.path.exists(self.image_path):
            logger.warning(f"背景图片路径不存在：{self.image_path}")
            return

        try:
            # 加载原始图片并转换格式（仅加载一次）
            self.original_image = QImage(self.image_path).convertToFormat(QImage.Format.Format_RGBA8888)
            # 初始调整大小（触发首次渲染）
            self._update_background_size(self.bg_label.parent().size())
        except Exception as e:
            logger.error(f"加载背景图片失败: {e}")
            # print(f"加载背景图片失败: {e}")

    def on_window_resized(self, new_size: QSize):
        """窗口大小变化时更新背景图片尺寸（优化版：仅尺寸变化时渲染）"""
        self._update_background_size(new_size)

    def _update_background_size(self, size: QSize):
        """私有方法：调整图片尺寸并设置到标签（带缓存优化）"""
        # 尺寸未变化时直接使用缓存
        if size == self.cached_size and not self.cached_pixmap.isNull():
            self.bg_label.setPixmap(self.cached_pixmap)
            self.bg_label.setGeometry(0, 0, size.width(), size.height())
            return
        
        # 尺寸变化时重新缩放
        scaled_image = self.original_image.scaled(
            size,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        # 更新缓存
        self.cached_pixmap = QPixmap.fromImage(scaled_image)
        self.cached_size = size

        # 应用新图片
        self.bg_label.setPixmap(self.cached_pixmap)
        self.bg_label.setGeometry(0, 0, size.width(), size.height())