import os
import time
from PySide6.QtCore import QMimeData, Qt, QUrl, QPoint, QEvent, QObject
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QTreeWidget, QApplication

class DragDropHandler(QObject):
    def __init__(self, file_list: QTreeWidget, main_window):
        super().__init__()  # 调用 QObject 父类构造函数
        self.file_list = file_list
        self.main_window = main_window
        self.drag_start_pos = QPoint()  # 存储起始位置（鼠标/触摸共用）
        self.drag_start_time = 0        # 存储起始时间戳（鼠标/触摸共用）
        self.is_touch = False           # 标记是否为触摸操作
        self._init_drag()

    def _init_drag(self):
        """初始化拖放配置（同时绑定鼠标和触摸事件）"""
        self.file_list.setDragEnabled(True)
        self.file_list.setDragDropMode(QTreeWidget.DragOnly)
        # 安装事件过滤器（替代直接重写touchEvent）
        self.file_list.installEventFilter(self)
        # 重写鼠标事件
        self.file_list.mousePressEvent = self.custom_mouse_press_event
        self.file_list.mouseMoveEvent = self.custom_mouse_move_event
        # 新增：重写触摸事件
        # self.file_list.touchEvent = self.custom_touch_event
    def eventFilter(self, obj, event):
        """事件过滤器：处理触摸事件"""
        # print(f"[DragDropHandler] 事件过滤器拦截事件类型: {event.type().name}")
        # if obj != self.file_list:
        #     print(f"[DragDropHandler] 接收到事件类型: {event.type().name}")
        if obj == self.file_list:
            if event.type() == QEvent.TouchBegin:
                self._handle_touch_begin(event)
                print("检测到触摸开始事件")
            elif event.type() == QEvent.TouchUpdate:
                self._handle_touch_update(event)
            # 其他事件传递给默认处理
        return super().eventFilter(obj, event)
    def _handle_touch_update(self, event):
        """处理触摸移动事件（原custom_touch_event的TouchUpdate逻辑）"""
        print("[TouchEvent] 类型: TouchUpdate")  # 调试日志
        touch_point = event.touchPoints()[0]
        current_pos = touch_point.pos().toPoint()
        print(f"[TouchUpdate] 当前位置: {current_pos}, 已移动时间: {(time.time() - self.drag_start_time):.2f}秒")

        should_trigger = self._should_trigger_touch_drag(event)
        print(f"[TouchUpdate] 是否触发拖放: {should_trigger}")

        if should_trigger:
            self._handle_touch_drag(event)
            print("[TouchUpdate] 触发拖放，事件被拦截")
            return  # 拦截事件（不传递给默认处理）
    def custom_mouse_press_event(self, event):
        """仅处理鼠标按下事件（QMouseEvent）"""
        if event.button() == Qt.LeftButton:  # 鼠标左键按下
            # 记录鼠标起始位置和时间（无需依赖额外标记，直接通过事件类型区分）
            self.drag_start_pos = event.pos()
            self.drag_start_time = time.time()
        super(self.file_list.__class__, self.file_list).mousePressEvent(event)

    def custom_touch_event(self, event):
        """仅处理触摸事件（QTouchEvent）"""
        # 调试：打印触摸事件类型
        print(f"[TouchEvent] 类型: {event.type().name}")  # 新增调试日志

        if event.type() == QEvent.TouchBegin:
            # 记录触摸起始位置和时间（直接通过事件类型区分）
            touch_point = event.touchPoints()[0]
            self.drag_start_pos = touch_point.pos().toPoint()
            self.drag_start_time = time.time()
            # 调试：打印触摸起始位置
            # print(f"[TouchBegin] 起始位置: {self.drag_start_pos}, 时间戳: {self.drag_start_time:.2f}")  # 新增调试日志
        elif event.type() == QEvent.TouchUpdate:
            # 调试：打印触摸移动信息
            touch_point = event.touchPoints()[0]
            current_pos = touch_point.pos().toPoint()
            print(f"[TouchUpdate] 当前位置: {current_pos}, 已移动时间: {(time.time() - self.drag_start_time):.2f}秒")  # 新增调试日志

            # 检查是否满足拖放条件（调试：打印判断结果）
            should_trigger = self._should_trigger_touch_drag(event)
            print(f"[TouchUpdate] 是否触发拖放: {should_trigger}")  # 新增调试日志

            if should_trigger:
                self._handle_touch_drag(event)
                print("[TouchUpdate] 触发拖放，事件被拦截")  # 新增调试日志
                return  # 触发拖放后不再传递事件
        # 传递所有触摸事件给默认处理（包括TouchUpdate触发滚动）
        result = super(type(self.file_list), self.file_list).event(event)  # 显式获取事件处理结果
        # 调试：打印事件传递结果
        print(f"[TouchEvent] 事件传递结果: {result}")  # 新增调试日志
        return result

    def _should_trigger_touch_drag(self, event):
        """判断是否应触发触摸拖放（新增逻辑）"""
        touch_point = event.touchPoints()[0]
        move_distance = (touch_point.pos().toPoint() - self.drag_start_pos).manhattanLength()
        time_elapsed = time.time() - self.drag_start_time

        # 调试：打印当前阈值和计算值
        print(f"[TouchDragCheck] 移动距离: {move_distance}px（阈值: {QApplication.startDragDistance()*2}px）, 已耗时: {time_elapsed:.2f}秒（阈值: 0.5秒）")  # 新增调试日志

        return (move_distance >= QApplication.startDragDistance() * 2 and
                time_elapsed > 0.5 and
                abs(touch_point.pos().x() - self.drag_start_pos.x()) > abs(touch_point.pos().y() - self.drag_start_pos.y()))

    def custom_mouse_move_event(self, event):
        """鼠标移动事件：仅处理鼠标操作（原有逻辑优化）"""
        if not self.is_touch and event.buttons() == Qt.LeftButton:
            self._handle_mouse_drag(event)
        else:
            # 关键修复：未满足拖放条件时，触发默认滚动逻辑
            print("触摸滑动事件")
            super(self.file_list.__class__, self.file_list).mouseMoveEvent(event)

    def _handle_mouse_drag(self, event):
        """独立鼠标拖放逻辑（与触摸区分）"""
        move_distance = (event.pos() - self.drag_start_pos).manhattanLength()
        time_elapsed = time.time() - self.drag_start_time

        # 鼠标逻辑：0.2秒后移动触发拖放（原有条件）
        if (move_distance >= QApplication.startDragDistance() and
            time_elapsed > 0.2 and
            abs(event.pos().x() - self.drag_start_pos.x()) > abs(event.pos().y() - self.drag_start_pos.y())):
            self._trigger_drag()

    def _handle_touch_drag(self, event):
        """新增：独立触摸拖放逻辑"""
        touch_point = event.touchPoints()[0]
        move_distance = (touch_point.pos().toPoint() - self.drag_start_pos).manhattanLength()
        time_elapsed = time.time() - self.drag_start_time

        # 触摸逻辑：0.3秒后移动触发拖放（阈值与鼠标不同）
        if (move_distance >= QApplication.startDragDistance() * 1.5 and
            time_elapsed > 0.3 and
            abs(touch_point.pos().x() - self.drag_start_pos.x()) > abs(touch_point.pos().y() - self.drag_start_pos.y())):
            self._trigger_drag()

    def _trigger_drag(self):
        """统一拖放触发逻辑（复用原有代码）"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return

        file_paths = []
        for item in selected_items:
            file_name = item.text(0)
            file_path = os.path.join(self.main_window.current_path, file_name)
            if os.path.exists(file_path):
                file_paths.append(file_path)

        if not file_paths:
            return

        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(path) for path in file_paths])

        drag = QDrag(self.file_list)
        drag.setMimeData(mime_data)
        first_item = selected_items[0]
        drag.setPixmap(first_item.icon(0).pixmap(32, 32))
        drag.exec(Qt.CopyAction)
    def _handle_touch_begin(self, event):
        """处理触摸开始事件（记录起始位置和时间）"""
        # 调试：打印触摸开始事件
        print("[TouchEvent] 类型: TouchBegin")
        # 记录触摸起始位置和时间（与原 custom_touch_event 的 TouchBegin 逻辑一致）
        touch_point = event.touchPoints()[0]
        self.drag_start_pos = touch_point.pos().toPoint()
        self.drag_start_time = time.time()
        # print(f"[TouchBegin] 起始位置: {self.drag_start_pos}, 时间戳: {self.drag_start_time:.2f}")  # 调试日志