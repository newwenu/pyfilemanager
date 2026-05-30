"""
数值滑块组件

替代 QSpinBox，提供更直观的调节方式
- 滑块拖动调节
- 预设按钮快速设置
- 实时数值显示
"""
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QSlider, 
                               QLabel, QPushButton, QSpinBox, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QFont


class ValueSlider(QWidget):
    """数值滑块组件
    
    结合滑块、数值显示和预设按钮
    """
    
    valueChanged = Signal(int)
    
    def __init__(self, min_val=16, max_val=128, step=8, default_val=40, 
                 unit="px", presets=None, parent=None, label=""):
        """
        Args:
            min_val: 最小值
            max_val: 最大值
            step: 步长
            default_val: 默认值
            unit: 单位（px, pt 等）
            presets: 预设值列表 [(label, value), ...]
            label: 左侧文字标签
        """
        super().__init__(parent)
        
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.unit = unit
        self.presets = presets or []
        self._label_text = label
        
        self._init_ui(default_val)
        
    def _init_ui(self, default_val):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 第一行：标签 + 滑块 + 数值显示
        slider_layout = QHBoxLayout()
        slider_layout.setSpacing(12)
        
        # 左侧文字标签
        if self._label_text:
            self.title_label = QLabel(self._label_text)
            self.title_label.setFixedWidth(90)
            slider_layout.addWidget(self.title_label)
        
        # 滑块
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(self.min_val, self.max_val)
        self.slider.setSingleStep(self.step)
        self.slider.setPageStep(self.step * 2)
        self.slider.setValue(default_val)
        self.slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                border-radius: 2px;
                background: rgba(128, 128, 128, 80);
            }
            QSlider::handle:horizontal {
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
                background: #4a9eff;
            }
        """)
        slider_layout.addWidget(self.slider, stretch=1)
        
        # 数值显示（使用 QSpinBox 但只读显示）
        self.value_display = QSpinBox()
        self.value_display.setRange(self.min_val, self.max_val)
        self.value_display.setSingleStep(self.step)
        self.value_display.setValue(default_val)
        self.value_display.setSuffix(f" {self.unit}")
        self.value_display.setFixedWidth(70)
        self.value_display.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)  # 隐藏上下按钮
        self.value_display.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 不获取焦点
        slider_layout.addWidget(self.value_display)
        
        # 重置按钮
        self.reset_btn = QPushButton("⟲")
        self.reset_btn.setFixedSize(24, 24)
        self.reset_btn.setToolTip("重置为默认值")
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #888;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(128, 128, 128, 40);
                border-radius: 12px;
                color: #fff;
            }
            QPushButton:pressed {
                background-color: rgba(128, 128, 128, 70);
                border-radius: 12px;
            }
        """)
        slider_layout.addWidget(self.reset_btn)
        
        layout.addLayout(slider_layout)
        
        # 第二行：预设按钮
        if self.presets:
            preset_layout = QHBoxLayout()
            preset_layout.setSpacing(6)
            preset_layout.addStretch()
            
            for label, value in self.presets:
                btn = QPushButton(label)
                btn.setProperty("preset_value", value)
                btn.setFixedHeight(24)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(128, 128, 128, 30);
                        border: 1px solid rgba(128, 128, 128, 50);
                        border-radius: 4px;
                        padding: 2px 10px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: rgba(128, 128, 128, 50);
                    }
                    QPushButton:pressed {
                        background-color: rgba(128, 128, 128, 70);
                    }
                """)
                btn.clicked.connect(self._on_preset_clicked)
                preset_layout.addWidget(btn)
            
            preset_layout.addStretch()
            layout.addLayout(preset_layout)
        
        self.setLayout(layout)
        
        # 屏蔽滑块和数值输入框的鼠标滚轮事件（防止在设置页面滚动时误触）
        self.slider.installEventFilter(self)
        self.value_display.installEventFilter(self)
        
        # 连接信号
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.value_display.valueChanged.connect(self._on_display_changed)
        self.reset_btn.clicked.connect(self._on_reset)
        
        self._default_value = default_val
        
    def eventFilter(self, obj, event):
        if obj in (self.slider, self.value_display) and event.type() == QEvent.Type.Wheel:
            event.ignore()
            return True
        return super().eventFilter(obj, event)

    def _on_slider_changed(self, value):
        """滑块值改变"""
        # 对齐到步长
        aligned_value = round(value / self.step) * self.step
        if aligned_value != value:
            self.slider.setValue(aligned_value)
            return
        
        self.value_display.setValue(value)
        self.valueChanged.emit(value)
        
    def _on_display_changed(self, value):
        """显示值改变（用户直接输入）"""
        self.slider.setValue(value)
        self.valueChanged.emit(value)
        
    def _on_preset_clicked(self):
        """预设按钮点击"""
        btn = self.sender()
        value = btn.property("preset_value")
        self.slider.setValue(value)
        
    def _on_reset(self):
        """重置为默认值"""
        self.slider.setValue(self._default_value)
        
    def value(self):
        """获取当前值"""
        return self.slider.value()
        
    def setValue(self, value):
        """设置值"""
        self.slider.setValue(value)


class IconSizeSlider(ValueSlider):
    """图标大小滑块（专用预设）"""
    
    def __init__(self, default_val=40, parent=None, label=""):
        presets = [
            ("小", 24),
            ("中", 40),
            ("大", 64),
            ("超大", 96)
        ]
        super().__init__(
            min_val=16, 
            max_val=128, 
            step=1, 
            default_val=default_val,
            unit="px",
            presets=presets,
            parent=parent,
            label=label
        )


class FontSizeSlider(ValueSlider):
    """字体大小滑块（专用预设）"""
    
    def __init__(self, default_val=15, parent=None, label=""):
        presets = [
            ("小", 12),
            ("中", 15),
            ("大", 18),
            ("特大", 22)
        ]
        super().__init__(
            min_val=8, 
            max_val=24, 
            step=1, 
            default_val=default_val,
            unit="pt",
            presets=presets,
            parent=parent,
            label=label
        )
