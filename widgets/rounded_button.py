from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import (QPainter, QPainterPath, QColor, QPalette,
                           QRadialGradient, QGradient)  # 新增渐变导入
from PySide6.QtCore import Qt, QEvent, QTimer, QPointF

class AntiAliasRoundedButton(QPushButton):
    """自定义抗锯齿露珠效果按钮类"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._bg_color = QColor(250, 250, 250, 120)  # 提高基础透明度（更通透）
        self._radius = 20  # 减小基础圆角（更接近露珠形状）
        self._hovered = False
        
        # 液体效果参数（优化）
        self._wave_offset = 0
        self._wave_amplitude = 2  # 更小振幅（更细腻）
        self._wave_frequency = 0.3  # 调整频率（更自然）
        
        # 动画定时器（60fps）
        self._animation_timer = QTimer(self)
        self._animation_timer.setInterval(16)
        self._animation_timer.timeout.connect(self._update_wave)

    def _update_wave(self):
        """更新波浪偏移量并触发重绘"""
        self._wave_offset += 0.2  # 调整此值控制波浪速度
        self.update()

    def set_bg_color(self, color: QColor):
        """设置背景色"""
        self._bg_color = color

    def set_radius(self, radius: int):
        """设置基础圆角半径"""
        self._radius = radius

    def enterEvent(self, event: QEvent):
        """重写鼠标进入事件：启动动画"""
        self._hovered = True
        self._animation_timer.start()
        self.update()

    def leaveEvent(self, event: QEvent):
        """重写鼠标离开事件：停止动画并重置"""
        self._hovered = False
        self._animation_timer.stop()
        self._wave_offset = 0  # 重置偏移量
        self.update()

    def _create_liquid_path(self):
        """生成液体效果路径（波浪形边缘）"""
        rect = self.rect()
        path = QPainterPath()
        
        # 顶部和底部使用基础圆角，左右两侧添加波浪
        start_x = rect.left()
        end_x = rect.right()
        center_y = rect.center().y()
        
        # 左侧波浪点
        left_point = QPointF(start_x, rect.top() + self._radius)
        # 右侧波浪点（根据偏移量计算Y坐标）
        right_y = rect.top() + self._radius + self._wave_amplitude * \
                 (1 + self._wave_amplitude * (self._wave_frequency * self._wave_offset))
        right_point = QPointF(end_x, right_y)
        
        # 构建波浪路径（简化示例，可根据需求调整贝塞尔曲线参数）
        path.moveTo(start_x, rect.top() + self._radius)
        path.quadTo(rect.center().x(), rect.top() - self._wave_amplitude, 
                   end_x, rect.top() + self._radius)  # 顶部波浪
        path.lineTo(end_x, rect.bottom() - self._radius)
        path.quadTo(rect.center().x(), rect.bottom() + self._wave_amplitude, 
                   start_x, rect.bottom() - self._radius)  # 底部波浪
        path.closeSubpath()
        
        return path

    def _create_dew_path(self):
        """生成露珠形状路径（更圆润的边缘）"""
        rect = self.rect()
        path = QPainterPath()
        # 使用更大的圆角模拟露珠的圆润感
        path.addRoundedRect(rect.adjusted(2, 2, -2, -2), 18, 18)  # 内缩2px更立体
        return path

    def paintEvent(self, event):
        """重写绘制事件，实现露珠效果"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 背景色（悬停时加深透明度）
        base_bg = self._bg_color if not self._hovered else \
                 QColor(self._bg_color.red(), self._bg_color.green(), 
                        self._bg_color.blue(), 180)  # 悬停时更不透明
        
        # 关键修复：正确生成路径对象（避免None）
        if self._hovered:
            path = self._create_dew_path()
        else:
            path = QPainterPath()  # 创建空路径对象
            path.addRoundedRect(self.rect(), self._radius, self._radius)  # 填充圆角矩形

        painter.fillPath(path, base_bg)  # 现在path一定是QPainterPath对象

        # 关键新增：绘制露珠高光（径向渐变）
        if self._hovered:
            # 高光位置随波浪偏移量轻微浮动
            highlight_center = QPointF(
                self.rect().center().x() + self._wave_offset * 1.5,
                self.rect().top() + 10  # 固定在顶部区域
            )
            gradient = QRadialGradient(highlight_center, 12)  # 高光半径12px
            gradient.setColorAt(0, QColor(255, 255, 255, 180))  # 中心最亮
            gradient.setColorAt(1, QColor(255, 255, 255, 0))    # 边缘透明
            gradient.setSpread(QGradient.Spread.ReflectSpread)  # 渐变扩散方式
            painter.fillPath(path, gradient)  # 在原有路径上叠加高光

        # 绘制按钮文字（保持原有居中逻辑）
        painter.setPen(self.palette().color(QPalette.ButtonText))
        painter.setFont(self.font())
        text_rect = self.rect()
        text_rect.adjust(0, -3, 0, 0)
        painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignVCenter, self.text())
