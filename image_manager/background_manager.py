import os
from PySide6.QtGui import QImage, QPixmap, Qt
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QLabel

class BackgroundManager:
    def __init__(self, bg_label: QLabel, image_path: str):
        self.bg_label = bg_label  # 背景标签控件
        self.image_path = image_path  # 背景图片路径
        self.original_image = QImage()  # 缓存原始图片

    def load_background(self):
        """加载并初始化背景图片（不含含透明度调整）"""
        if not os.path.exists(self.image_path):
            print(f"警告：背景图片路径不存在：{self.image_path}")
            return

        try:
            # 加载原始图片并转换格式
            self.original_image = QImage(self.image_path).convertToFormat(QImage.Format.Format_RGBA8888)
            # 初始调整大小
            self._update_background_size(self.bg_label.parent().size())
        except Exception as e:
            print(f"加载背景图片失败: {e}")

    def on_window_resized(self, new_size: QSize):
        """窗口大小变化时更新背景图片尺寸"""
        self._update_background_size(new_size)

    def _update_background_size(self, size: QSize):
        """私有方法：调整图片尺寸并设置到标签"""
        # 缩放图片适配窗口
        scaled_image = self.original_image.scaled(
            size,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        # 可选：调整透明度（示例中注释掉，根据需求启用）
        # for y in range(scaled_image.height()):
        #     for x in range(scaled_image.width()):
        #         color = scaled_image.pixelColor(x, y)
        #         color.setAlpha(178)  # 0.7透明度
        #         scaled_image.setPixelColor(x, y, color)
        # 设置图片到标签
        self.bg_label.setPixmap(QPixmap.fromImage(scaled_image))
        self.bg_label.setGeometry(0, 0, size.width(), size.height())

    def load_background_origin(self):
        """优化后的背景加载：使用 QLabel 作为背景层，支持自动适配窗口大小"""
        try:
            # 加载原始图片并调整透明度
            image = QImage(self.image_path).convertToFormat(QImage.Format.Format_RGBA8888)
            # 调整透明度（0-255，0.7 透明度对应 255*0.7≈178）
            image = image.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            for y in range(image.height()):
                for x in range(image.width()):
                    color = image.pixelColor(x, y)
                    # color.setAlpha(178)  # 直接设置透明度值
                    image.setPixelColor(x, y, color)
            
            # 设置背景标签图片
            self.bg_label.setPixmap(QPixmap.fromImage(image))
            self.bg_label.setGeometry(0, 0, self.width(), self.height())  # 初始位置
            
        except Exception as e:
            print(f"加载背景图片失败: {e}")

