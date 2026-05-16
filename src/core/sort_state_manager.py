"""
排序状态管理器 - 统一管理排序状态（应用生命周期内有效）

功能：
1. 统一管理排序状态（列、方向、文件夹归并、文件夹在前）
2. 提供状态变化信号
3. 支持状态历史（撤销功能）

注意：排序状态仅在应用运行期间有效，重启后恢复默认
"""
from PySide6.QtCore import QObject, Signal
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class SortState:
    """排序状态数据类"""
    column: int = 0           # 排序列索引
    key: str = "name"         # 排序键 (name/size/mtime)
    reverse: bool = False     # 是否降序
    folders_grouped: bool = True  # 文件夹归并（将文件夹归在一起）
    folders_before: bool = True   # 文件夹在前（文件夹排在文件前面）
    
    def __eq__(self, other):
        if not isinstance(other, SortState):
            return False
        return (self.column == other.column and 
                self.key == other.key and 
                self.reverse == other.reverse and
                self.folders_grouped == other.folders_grouped and
                self.folders_before == other.folders_before)


class SortStateManager(QObject):
    """
    排序状态管理器 - 单例模式
    
    职责：
    1. 统一管理排序状态（应用生命周期内）
    2. 提供状态变化信号
    3. 支持撤销操作
    """
    
    # 信号
    state_changed = Signal(SortState)  # 排序状态变化
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        self._initialized = True
        
        # 初始化默认状态
        self._state = SortState()
        self._history: List[SortState] = []  # 状态历史（支持撤销）
        self._history_index = -1
        self._max_history = 10
    
    @property
    def state(self) -> SortState:
        """获取当前排序状态"""
        return self._state
    
    def set_sort_column(self, column: int, key: str):
        """
        设置排序列
        
        如果列变化，默认使用升序
        如果列相同，切换排序方向
        """
        new_state = SortState(
            column=column,
            key=key,
            reverse=self._state.reverse if self._state.column == column else False,
            folders_grouped=self._state.folders_grouped,
            folders_before=self._state.folders_before
        )
        
        # 如果列相同，切换方向
        if self._state.column == column:
            new_state.reverse = not self._state.reverse
        
        self._set_state(new_state)
    
    def set_sort_order(self, reverse: bool):
        """设置排序方向"""
        if self._state.reverse != reverse:
            new_state = SortState(
                column=self._state.column,
                key=self._state.key,
                reverse=reverse,
                folders_grouped=self._state.folders_grouped,
                folders_before=self._state.folders_before
            )
            self._set_state(new_state)
    
    def toggle_folders_grouped(self):
        """切换文件夹归并"""
        new_state = SortState(
            column=self._state.column,
            key=self._state.key,
            reverse=self._state.reverse,
            folders_grouped=not self._state.folders_grouped,
            folders_before=self._state.folders_before
        )
        self._set_state(new_state)
    
    def toggle_folders_before(self):
        """切换文件夹在前"""
        new_state = SortState(
            column=self._state.column,
            key=self._state.key,
            reverse=self._state.reverse,
            folders_grouped=self._state.folders_grouped,
            folders_before=not self._state.folders_before
        )
        self._set_state(new_state)
    
    def _set_state(self, new_state: SortState):
        """设置新状态（内部方法）"""
        if self._state == new_state:
            return
        
        # 保存到历史
        self._add_to_history(self._state)
        
        # 更新状态
        self._state = new_state
        
        # 发送信号
        self.state_changed.emit(self._state)
    
    def _add_to_history(self, state: SortState):
        """添加到历史"""
        # 删除当前位置之后的历史
        self._history = self._history[:self._history_index + 1]
        
        # 添加新状态
        self._history.append(state)
        
        # 限制历史长度
        if len(self._history) > self._max_history:
            self._history.pop(0)
        else:
            self._history_index += 1
    
    def can_undo(self) -> bool:
        """是否可以撤销"""
        return self._history_index >= 0
    
    def undo(self) -> Optional[SortState]:
        """撤销到上一个状态"""
        if not self.can_undo():
            return None
        
        # 恢复到上一个状态
        self._state = self._history[self._history_index]
        self._history_index -= 1
        
        # 发送信号
        self.state_changed.emit(self._state)
        
        return self._state
    
    def reset(self):
        """重置为默认状态"""
        self._set_state(SortState())
        self._history.clear()
        self._history_index = -1
