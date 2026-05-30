"""
配置提供者模块 - 提供全局配置访问

使用单例模式，支持：
- 全局配置访问
- 配置变更事件通知
- 动态配置重载
- 临时编辑会话（支持撤销/提交）
"""
from typing import Any, Callable, Optional
from .event_bus import event_bus


class ConfigProvider:
    """
    配置提供者 - 单例模式
    
    提供全局配置访问，配置变更时自动触发事件
    支持临时编辑会话：在会话中的修改只保存在内存，可一键撤销或提交
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if ConfigProvider._initialized:
            return
        self._config = {}
        self._observers = {}  # key -> list of callbacks
        self._config_manager = None  # 绑定 ConfigManager 实现自动落盘
        # 临时编辑会话相关
        self._session_active = False
        self._session_backup = {}  # 会话开始时备份的原始配置
        self._session_modified_keys = set()  # 会话中被修改过的 key
        ConfigProvider._initialized = True

    def bind_config_manager(self, config_manager):
        """绑定 ConfigManager，set() 时自动持久化到磁盘"""
        self._config_manager = config_manager
    
    def load(self, config_dict: dict):
        """
        加载配置
        
        Args:
            config_dict: 配置字典
        """
        self._config = config_dict.copy()
    
    def get(self, key: str, default=None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
        
        Returns:
            配置值或默认值
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any, emit_event: bool = True, persist: bool = True):
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
            emit_event: 是否触发事件
            persist: 是否持久化到磁盘（False 时仅更新内存；会话期间即使为 True 也不会落盘）
        """
        old_value = self._config.get(key)
        self._config[key] = value

        # 追踪会话修改
        if self._session_active and old_value != value:
            self._session_modified_keys.add(key)

        # 只有值改变时才触发事件
        if old_value != value:
            # 通知观察者
            if key in self._observers:
                for callback in self._observers[key]:
                    callback(key, value)

            # 触发全局事件
            if emit_event:
                event_bus.config_changed.emit(key, value)

        # 自动持久化到磁盘（会话期间不落盘，由 commit_session 统一处理）
        if persist and not self._session_active and self._config_manager is not None:
            self._config_manager.set_setting(key, value)
            self._config_manager.save_config()
    
    # ========== 临时编辑会话（用于设置对话框等场景） ==========

    def begin_session(self) -> dict:
        """
        开始临时编辑会话

        在会话期间，所有修改只保存在内存中（即使 persist=True 也不会写入磁盘）。
        可通过 rollback_session() 撤销所有修改，或通过 commit_session() 提交到磁盘。

        Returns:
            当前配置的副本（作为初始的对比基准）
        """
        self._session_snapshot = self._config.copy()  # 用于星形指示器对比的基准
        self._session_modified_keys.clear()
        self._session_active = True
        return self._session_snapshot.copy()

    def update_session_snapshot(self) -> dict:
        """
        更新会话快照为当前配置值

        在点击"应用"后调用，将当前配置作为新的对比基准。
        这样星形指示器会对比当前值 vs 上次应用后的值。

        Returns:
            更新后的配置快照副本
        """
        # 即使会话不活跃（已提交），也重新创建快照
        self._session_snapshot = self._config.copy()
        self._session_modified_keys.clear()
        # 重新激活会话，以便后续修改可以继续追踪
        self._session_active = True
        return self._session_snapshot.copy()

    def rollback_session(self) -> None:
        """
        撤销临时编辑会话中的所有修改，恢复到会话开始时的状态

        会触发 config_changed 事件通知各组件恢复
        """
        if not self._session_active:
            return

        # 恢复被修改的 key
        for key in self._session_modified_keys:
            old_value = self._session_snapshot.get(key)
            current_value = self._config.get(key)

            if old_value != current_value:
                self._config[key] = old_value
                # 通知观察者
                if key in self._observers:
                    for callback in self._observers[key]:
                        callback(key, old_value)
                # 触发全局事件
                event_bus.config_changed.emit(key, old_value)

        # 清理会话状态
        self._session_active = False
        self._session_snapshot.clear()
        self._session_modified_keys.clear()

    def commit_session(self, emit_event: bool = True) -> None:
        """
        提交临时编辑会话中的所有修改到磁盘

        Args:
            emit_event: 是否触发 config_changed 事件
        """
        if not self._session_active:
            return

        # 找出实际变更的 key
        changed_keys = []
        for key in self._session_modified_keys:
            snapshot_value = self._session_snapshot.get(key)
            current_value = self._config.get(key)
            if snapshot_value != current_value:
                changed_keys.append(key)

        # 持久化到磁盘
        if self._config_manager is not None:
            for key in changed_keys:
                self._config_manager.set_setting(key, self._config[key])
            if changed_keys:
                self._config_manager.save_config()

        # 触发事件（如果需要）
        if emit_event:
            for key in changed_keys:
                event_bus.config_changed.emit(key, self._config[key])

        # 清理会话状态
        self._session_active = False
        self._session_snapshot.clear()
        self._session_modified_keys.clear()

    def is_session_active(self) -> bool:
        """检查是否有活跃的临时编辑会话"""
        return self._session_active

    def get_session_snapshot(self, key: str, default=None) -> Any:
        """
        获取会话快照中某个 key 的值

        用于星形指示器对比：当前值 vs 上次应用/开始时的值
        """
        if not self._session_active:
            return self._config.get(key, default)
        return self._session_snapshot.get(key, self._config.get(key, default))

    def get_session_modified_keys(self) -> set:
        """获取会话中被修改过的 key 集合"""
        return self._session_modified_keys.copy()
    
    # ========== 原有方法 ==========
    
    def reload(self, config_dict: dict):
        """
        重新加载配置
        
        Args:
            config_dict: 新的配置字典
        """
        old_config = self._config.copy()
        self._config = config_dict.copy()
        
        # 找出变更的配置并触发事件
        all_keys = set(old_config.keys()) | set(self._config.keys())
        for key in all_keys:
            old_value = old_config.get(key)
            new_value = self._config.get(key)
            if old_value != new_value:
                event_bus.config_changed.emit(key, new_value)
        
        # 触发重载事件
        event_bus.config_reload.emit()
    
    def observe(self, key: str, callback: Callable[[str, Any], None]):
        """
        观察配置变更
        
        Args:
            key: 要观察的配置键
            callback: 回调函数，接收 (key, value) 参数
        """
        if key not in self._observers:
            self._observers[key] = []
        self._observers[key].append(callback)
    
    def unobserve(self, key: str, callback: Callable[[str, Any], None]):
        """
        取消观察配置变更
        
        Args:
            key: 配置键
            callback: 回调函数
        """
        if key in self._observers and callback in self._observers[key]:
            self._observers[key].remove(callback)
    
    def get_all(self) -> dict:
        """获取所有配置（返回副本，修改不影响内部）"""
        return self._config.copy()
    
    def get_config(self) -> dict:
        """获取内部配置引用（返回实际 dict，用于 UI 组件实时读取）"""
        return self._config
    
    def has(self, key: str) -> bool:
        """检查配置是否存在"""
        return key in self._config


# 全局单例实例
config_provider = ConfigProvider()
