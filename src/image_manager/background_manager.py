import os
from PySide6.QtGui import QImage, QPixmap, Qt,QTransform
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import QSize,QTimer
from utils.logging_config import get_logger
from threads.webp_loader import WebpLoader
logger = get_logger(__name__)
class BackgroundManager:
    def __init__(self, bg_label: QLabel, image_path: str,random:bool=False):
        self.bg_label = bg_label  # 背景标签控件
        self.image_path = None
        if os.path.exists(image_path):
            self.image_path = image_path
        if random:
            self._start_webp_loading()
            # self.image_path = get_webp()
        
        self.original_image = QImage()  # 缓存原始图片
        self.cached_size = QSize()  # 新增：缓存最后一次渲染的尺寸
        self.cached_pixmap = QPixmap()  # 新增：缓存渲染后的图片

    def _start_webp_loading(self):
        """启动异步加载网络图片"""
        self._set_temp_label(self)
        
        # 设置3秒后自动清除（无论成功与否）
        QTimer.singleShot(3000, self._clear_temp_label)
        self.thread = WebpLoader()
        self.thread.loaded.connect(self._on_webp_loaded)
        self.thread.start()

    def _set_temp_label(self,parent):
        """创建临时标签"""
        # 创建临时提示标签
        self.temp_label = QLabel(parent.bg_label)
        self.temp_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        # 调整边距使内容不贴边
        self.temp_label.setContentsMargins(0, 0, 10, 10)
        self.temp_label.setStyleSheet("""
            QLabel {
                color: white;
                background: rgba(0, 0, 0, 120);
                padding: 4px 8px;
                border-radius: 8px;
                margin: 6px;
            }
        """)
        self._update_temp_label("⏳ 加载中...")

    def _on_webp_loaded(self, path):
        """网络图片加载完成回调（新增有效性检查）"""
        if path and os.path.exists(path):
            self.image_path = path
            self.load_background()
            self._update_temp_label("✅ 加载成功")
            QTimer.singleShot(2000, self._clear_temp_label)
        else:
            logger.warning("网络图片加载失败，保持原有背景")
            self._set_temp_label(self,"⚠️ 加载失败")
            QTimer.singleShot(3000, self._clear_temp_label)
        # if hasattr(self, 'temp_label'):
        #     if path and os.path.exists(path):
        #         self._update_temp_label("✅ 加载成功")
        #         QTimer.singleShot(2000, self._clear_temp_label)
        #     else:
        #         self._update_temp_label("⚠️ 加载失败")
        #         QTimer.singleShot(3000, self._clear_temp_label)

    def _update_temp_label(self, text):
        """更新临时标签内容"""
        if hasattr(self, 'temp_label') and self.temp_label:
            self.temp_label.setText(text)
            self.temp_label.adjustSize()  # 自动调整标签尺寸

    def _clear_temp_label(self):
        """清除临时标签"""
        if hasattr(self, 'temp_label') and self.temp_label:
            self.temp_label.deleteLater()
            del self.temp_label

    def load_background(self):
        """加载并初始化背景图片（优化版：含尺寸缓存）"""
        if not os.path.exists(self.image_path):
            logger.warning(f"背景图片路径不存在：{self.image_path}")
            return

        try:
            # 加载原始图片并转换格式（仅加载一次）
            self.original_image = QImage(self.image_path).convertToFormat(QImage.Format.Format_RGBA8888)
            # 新增：获取图片尺寸信息
            width = self.original_image.width()
            height = self.original_image.height()
            if width<height:
                self.original_image = self.original_image.transformed(QTransform().rotate(90))
            # logger.info(f"图片尺寸: {width}x{height} (宽x高)")
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
        # 应用新图片后强制更新临时标签位置
        self.temp_label.move(size.width() - self.temp_label.width() - 10, 
                           size.height() - self.temp_label.height() - 10)
        # 应用新图片
        self.bg_label.setPixmap(self.cached_pixmap)
        self.bg_label.setGeometry(0, 0, size.width(), size.height())