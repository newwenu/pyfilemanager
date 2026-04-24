"""
错误消息优化模块

将技术错误转换为用户友好的提示信息
支持多语言翻译，与 LanguageManager 同步
"""
import os
import errno
from typing import Optional, Dict, Callable


class ErrorMessageResolver:
    """错误消息解析器
    
    将异常转换为用户友好的错误消息
    自动同步应用程序语言设置
    """
    
    # 错误消息模板
    MESSAGES = {
        # 文件不存在
        'file_not_found': {
            'zh_CN': '找不到文件/文件夹: {name}',
            'en_US': 'File/Folder not found: {name}',
        },
        # 权限不足
        'permission_denied': {
            'zh_CN': '无法访问 {name}，请检查文件权限或以管理员身份运行',
            'en_US': 'Cannot access {name}, please check permissions or run as administrator',
        },
        # 文件已存在
        'file_exists': {
            'zh_CN': '{name} 已存在，请使用其他名称',
            'en_US': '{name} already exists, please use a different name',
        },
        # 磁盘空间不足
        'disk_full': {
            'zh_CN': '磁盘空间不足，无法完成操作',
            'en_US': 'Disk is full, cannot complete operation',
        },
        # 路径过长
        'path_too_long': {
            'zh_CN': '文件路径过长，请缩短文件名或移动到更浅的目录',
            'en_US': 'Path is too long, please shorten the name or move to a shallower directory',
        },
        # 文件被占用
        'file_in_use': {
            'zh_CN': '{name} 正在被其他程序使用，请关闭后重试',
            'en_US': '{name} is being used by another program, please close it and try again',
        },
        # 只读文件
        'read_only': {
            'zh_CN': '{name} 是只读文件，无法修改',
            'en_US': '{name} is read-only and cannot be modified',
        },
        # 网络路径不可用
        'network_error': {
            'zh_CN': '网络路径不可用，请检查网络连接',
            'en_US': 'Network path is not available, please check your connection',
        },
        # 循环引用（复制/移动到子目录）
        'recursive_operation': {
            'zh_CN': '无法将文件夹复制/移动到自身或其子目录中',
            'en_US': 'Cannot copy/move folder into itself or its subdirectories',
        },
        # 未知错误
        'unknown_error': {
            'zh_CN': '操作失败: {details}',
            'en_US': 'Operation failed: {details}',
        },
        # 操作成功
        'success_copy': {
            'zh_CN': '成功复制 {count} 个文件',
            'en_US': 'Successfully copied {count} files',
        },
        'success_move': {
            'zh_CN': '成功移动 {count} 个文件',
            'en_US': 'Successfully moved {count} files',
        },
        'success_delete': {
            'zh_CN': '成功删除 {count} 个文件到回收站',
            'en_US': 'Successfully deleted {count} files to recycle bin',
        },
        'success_rename': {
            'zh_CN': '重命名成功: {name}',
            'en_US': 'Successfully renamed to: {name}',
        },
        'success_create_folder': {
            'zh_CN': '创建成功: {name}',
            'en_US': 'Successfully created: {name}',
        },
        'success_clipboard_copy': {
            'zh_CN': '已复制 {count} 个文件到剪贴板',
            'en_US': 'Copied {count} files to clipboard',
        },
        'success_clipboard_cut': {
            'zh_CN': '已剪切 {count} 个文件到剪贴板',
            'en_US': 'Cut {count} files to clipboard',
        },
        'success_paste': {
            'zh_CN': '成功粘贴 {count} 个文件',
            'en_US': 'Successfully pasted {count} files',
        },
        # 部分失败
        'partial_failure': {
            'zh_CN': '部分操作失败:\n{details}',
            'en_US': 'Some operations failed:\n{details}',
        },
    }
    
    # 语言代码映射（将 LanguageManager 的语言代码映射到内部代码）
    LANG_MAP = {
        'zh_CN': 'zh_CN',
        'zh': 'zh_CN',
        'en_US': 'en_US',
        'en': 'en_US',
    }
    
    def __init__(self, language: str = 'zh_CN'):
        """
        Args:
            language: 语言代码，如 'zh_CN' 或 'en_US'
        """
        self._language = self._normalize_lang(language)
        self._language_provider: Optional[Callable[[], str]] = None
    
    def _normalize_lang(self, language: str) -> str:
        """标准化语言代码"""
        return self.LANG_MAP.get(language, 'zh_CN')
    
    def set_language(self, language: str) -> None:
        """设置语言"""
        self._language = self._normalize_lang(language)
    
    def set_language_provider(self, provider: Callable[[], str]) -> None:
        """设置语言提供者函数
        
        用于动态获取当前应用语言，与 LanguageManager 集成
        
        Args:
            provider: 返回当前语言代码的函数
        """
        self._language_provider = provider
    
    def _get_current_language(self) -> str:
        """获取当前语言"""
        if self._language_provider:
            return self._normalize_lang(self._language_provider())
        return self._language
    
    def _get_message(self, key: str, **kwargs) -> str:
        """获取格式化后的消息"""
        lang = self._get_current_language()
        message_dict = self.MESSAGES.get(key, self.MESSAGES['unknown_error'])
        message = message_dict.get(lang, message_dict['zh_CN'])
        try:
            return message.format(**kwargs)
        except KeyError:
            return message
    
    def resolve_exception(self, exception: Exception, path: str = "") -> str:
        """解析异常为用户友好消息
        
        Args:
            exception: 异常对象
            path: 相关文件路径
        
        Returns:
            用户友好的错误消息
        """
        name = os.path.basename(path) if path else "文件"
        error_code = getattr(exception, 'errno', None)
        error_str = str(exception).lower()
        
        # 根据错误类型和errno解析
        if isinstance(exception, PermissionError) or error_code == errno.EACCES:
            # 检查是否为只读
            if path and os.path.exists(path) and not os.access(path, os.W_OK):
                return self._get_message('read_only', name=name)
            return self._get_message('permission_denied', name=name)
        
        elif isinstance(exception, FileNotFoundError) or error_code == errno.ENOENT:
            return self._get_message('file_not_found', name=name)
        
        elif isinstance(exception, FileExistsError) or error_code == errno.EEXIST:
            return self._get_message('file_exists', name=name)
        
        elif error_code == errno.ENOSPC:
            return self._get_message('disk_full')
        
        elif error_code == errno.ENAMETOOLONG or 'too long' in error_str:
            return self._get_message('path_too_long')
        
        elif error_code in (errno.EBUSY, errno.EAGAIN) or 'being used' in error_str:
            return self._get_message('file_in_use', name=name)
        
        elif error_code == errno.EROFS:
            return self._get_message('read_only', name=name)
        
        elif 'network' in error_str or 'unc' in error_str:
            return self._get_message('network_error')
        
        elif 'same file' in error_str or 'recursive' in error_str:
            return self._get_message('recursive_operation')
        
        # 默认返回原始错误信息
        return self._get_message('unknown_error', details=str(exception))
    
    def success_message(self, operation: str, count: int = 1, name: str = "") -> str:
        """生成成功消息
        
        Args:
            operation: 操作类型 (copy, move, delete, rename, create_folder, clipboard_copy, clipboard_cut, paste)
            count: 数量
            name: 名称（用于rename和create_folder）
        """
        key_map = {
            'copy': 'success_copy',
            'move': 'success_move',
            'delete': 'success_delete',
            'rename': 'success_rename',
            'create_folder': 'success_create_folder',
            'clipboard_copy': 'success_clipboard_copy',
            'clipboard_cut': 'success_clipboard_cut',
            'paste': 'success_paste',
        }
        
        key = key_map.get(operation, 'unknown_error')
        
        if operation in ('rename', 'create_folder'):
            return self._get_message(key, name=name)
        else:
            return self._get_message(key, count=count)
    
    def partial_failure_message(self, details: str) -> str:
        """生成部分失败消息"""
        return self._get_message('partial_failure', details=details)


# 全局解析器实例
_resolver = ErrorMessageResolver()


def set_language(language: str) -> None:
    """设置全局语言"""
    _resolver.set_language(language)


def set_language_provider(provider: Callable[[], str]) -> None:
    """设置语言提供者函数，用于与 LanguageManager 集成"""
    _resolver.set_language_provider(provider)


def resolve_exception(exception: Exception, path: str = "") -> str:
    """解析异常为用户友好消息"""
    return _resolver.resolve_exception(exception, path)


def success_message(operation: str, count: int = 1, name: str = "") -> str:
    """生成成功消息"""
    return _resolver.success_message(operation, count, name)


def partial_failure_message(details: str) -> str:
    """生成部分失败消息"""
    return _resolver.partial_failure_message(details)


# 与 LanguageManager 集成的初始化函数
def init_with_language_manager(language_manager) -> None:
    """使用 LanguageManager 初始化错误消息模块
    
    Args:
        language_manager: LanguageManager 实例
    """
    # 设置语言提供者，动态获取当前语言
    set_language_provider(lambda: language_manager.lang)
    
    # 设置初始语言
    set_language(language_manager.lang)
