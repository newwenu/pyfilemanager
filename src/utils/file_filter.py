"""
文件过滤器模块 - 统一的文件过滤逻辑

支持：
- 系统保护文件排除（按属性，如Windows的S属性）
- 自定义路径排除
- 隐藏文件处理
- 跨平台适配（Windows/Linux/macOS）
"""

import os
import sys
import stat
from typing import List, Tuple, Optional

# Windows特定的导入
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

from core.service_locator import ServiceLocator


class FileFilter:
    """文件过滤器类 - 统一的文件过滤逻辑"""
    
    # Windows文件属性常量
    # FILE_ATTRIBUTE_SYSTEM = 0x4 (4)
    # FILE_ATTRIBUTE_HIDDEN = 0x2 (2)
    FILE_ATTRIBUTE_SYSTEM = 0x00000004
    FILE_ATTRIBUTE_HIDDEN = 0x00000002
    
    def __init__(self):
        self._cache_enabled = True
        self._exclude_cache: dict = {}
    
    def get_scan_excludes(self) -> Tuple[bool, List[str]]:
        """
        获取扫描排除配置
        
        Returns:
            (hide_protected, custom_paths)
            - hide_protected: 是否隐藏受系统保护的文件
            - custom_paths: 自定义排除路径列表
        """
        try:
            config_manager = ServiceLocator.get("config_manager")
            if not config_manager:
                return False, []
            
            # 获取是否隐藏受系统保护文件
            hide_protected = config_manager.get("scan_exclude_system_protected", False)
            
            # 获取自定义排除列表
            custom_excludes = config_manager.get("scan_exclude_custom", [])
            
            return hide_protected, custom_excludes
        except Exception:
            return False, []
    
    def _get_file_attributes_from_direntry(self, entry) -> int:
        """
        从DirEntry对象获取Windows文件属性
        
        Python 3.5+ 的 os.DirEntry 在 Windows 上会缓存文件属性
        可以通过 entry.stat() 获取，其中包含 st_file_attributes
        """
        try:
            # 使用 DirEntry.stat() 获取文件属性
            # 在 Windows 上，stat_result 包含 st_file_attributes
            stat_result = entry.stat(follow_symlinks=False)
            
            # Windows 的 stat 结果包含 st_file_attributes (Python 3.5+)
            if hasattr(stat_result, 'st_file_attributes'):
                return stat_result.st_file_attributes
            
            return -1
        except Exception:
            return -1
    
    def _get_file_attributes_ctypes(self, path: str) -> int:
        """使用ctypes获取Windows文件属性"""
        try:
            kernel32 = ctypes.windll.kernel32
            GetFileAttributesW = kernel32.GetFileAttributesW
            GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
            GetFileAttributesW.restype = wintypes.DWORD
            
            attrs = GetFileAttributesW(path)
            if attrs == 0xFFFFFFFF:  # INVALID_FILE_ATTRIBUTES
                return -1
            return attrs
        except Exception:
            return -1
    
    def is_system_protected(self, entry) -> bool:
        """
        检查文件/目录是否受系统保护
        
        Windows: 检查S属性 (FILE_ATTRIBUTE_SYSTEM)
        Linux/macOS: 检查文件权限和特殊属性
        
        Args:
            entry: os.DirEntry 对象或文件路径
            
        Returns:
            是否受系统保护
        """
        try:
            if sys.platform == "win32":
                # Windows: 优先使用DirEntry缓存的属性
                attrs = self._get_file_attributes_from_direntry(entry)
                
                if attrs != -1:
                    return bool(attrs & self.FILE_ATTRIBUTE_SYSTEM)
                
                # 如果DirEntry没有属性，使用ctypes作为备选
                if hasattr(entry, 'path'):
                    path = entry.path
                else:
                    path = str(entry)
                
                attrs = self._get_file_attributes_ctypes(path)
                if attrs != -1:
                    return bool(attrs & self.FILE_ATTRIBUTE_SYSTEM)
                
                # 无法获取属性，返回False
                return False
            else:
                # Linux/macOS: 检查文件权限和特殊属性
                if hasattr(entry, 'path'):
                    path = entry.path
                else:
                    path = str(entry)
                
                try:
                    file_stat = os.stat(path, follow_symlinks=False)
                    mode = file_stat.st_mode
                    
                    # 检查是否是系统关键目录或文件
                    is_system_only_writable = (
                        (mode & stat.S_IWUSR) and
                        not (mode & stat.S_IWGRP) and
                        not (mode & stat.S_IWOTH)
                    )
                    
                    has_special_bits = bool(mode & (stat.S_ISUID | stat.S_ISGID | stat.S_ISVTX))
                    is_root_owned = (file_stat.st_uid == 0)
                    
                    return is_root_owned and (is_system_only_writable or has_special_bits)
                    
                except (OSError, PermissionError):
                    return False
                    
        except Exception:
            return False
    
    def is_hidden(self, entry) -> bool:
        """
        检查文件/目录是否隐藏
        
        Windows: 检查H属性 (FILE_ATTRIBUTE_HIDDEN)
        Linux/macOS: 检查是否以.开头
        
        Args:
            entry: os.DirEntry 对象
            
        Returns:
            是否隐藏
        """
        try:
            # 首先检查是否以.开头（跨平台通用）
            name = entry.name if hasattr(entry, 'name') else os.path.basename(str(entry))
            if name.startswith('.'):
                return True
            
            # Windows额外检查H属性
            if sys.platform == "win32":
                # 优先使用DirEntry缓存的属性
                attrs = self._get_file_attributes_from_direntry(entry)
                
                if attrs != -1:
                    return bool(attrs & self.FILE_ATTRIBUTE_HIDDEN)
                
                # 备选：使用ctypes
                if hasattr(entry, 'path'):
                    path = entry.path
                else:
                    path = str(entry)
                
                attrs = self._get_file_attributes_ctypes(path)
                if attrs != -1:
                    return bool(attrs & self.FILE_ATTRIBUTE_HIDDEN)
            
            return False
        except Exception:
            return False
    
    def should_show(
        self, 
        entry, 
        show_hidden: bool = False,
        use_cache: bool = True
    ) -> bool:
        """
        判断文件/目录是否应该显示
        
        过滤顺序：
        1. 系统保护文件（按属性，如果启用）
        2. 自定义排除路径
        3. 隐藏文件（根据show_hidden参数）
        
        Args:
            entry: os.DirEntry 对象
            show_hidden: 是否显示隐藏文件
            use_cache: 是否使用缓存
            
        Returns:
            是否应该显示
        """
        entry_path = entry.path if hasattr(entry, 'path') else str(entry)
        entry_name = entry.name if hasattr(entry, 'name') else os.path.basename(entry_path)
        
        # 缓存检查
        if use_cache and self._cache_enabled:
            cache_key = (entry_path, show_hidden)
            if cache_key in self._exclude_cache:
                return self._exclude_cache[cache_key]
        
        # 获取排除配置
        hide_protected, custom_paths = self.get_scan_excludes()
        
        # 1. 检查系统保护文件（按属性）
        if hide_protected and self.is_system_protected(entry):
            result = False
            if use_cache and self._cache_enabled:
                self._exclude_cache[cache_key] = result
            return result
        
        # 2. 检查自定义排除路径
        for exclude_path in custom_paths:
            if entry_path == exclude_path or entry_path.startswith(exclude_path + os.sep):
                result = False
                if use_cache and self._cache_enabled:
                    self._exclude_cache[cache_key] = result
                return result
        
        # 3. 检查隐藏文件
        if not show_hidden and self.is_hidden(entry):
            result = False
            if use_cache and self._cache_enabled:
                self._exclude_cache[cache_key] = result
            return result
        
        result = True
        if use_cache and self._cache_enabled:
            self._exclude_cache[cache_key] = result
        return result
    
    def filter_entries(
        self, 
        entries: List, 
        show_hidden: bool = False
    ) -> List:
        """
        批量过滤条目
        
        Args:
            entries: 条目列表（os.DirEntry对象列表）
            show_hidden: 是否显示隐藏文件
            
        Returns:
            过滤后的条目列表
        """
        return [e for e in entries if self.should_show(e, show_hidden)]
    
    def clear_cache(self):
        """清除过滤缓存"""
        self._exclude_cache.clear()
    
    def set_cache_enabled(self, enabled: bool):
        """设置是否启用缓存"""
        self._cache_enabled = enabled
        if not enabled:
            self.clear_cache()


# 全局过滤器实例
_file_filter: Optional[FileFilter] = None


def get_file_filter() -> FileFilter:
    """获取全局文件过滤器实例"""
    global _file_filter
    if _file_filter is None:
        _file_filter = FileFilter()
    return _file_filter


def should_show(entry, show_hidden: bool = False) -> bool:
    """
    便捷函数：判断文件/目录是否应该显示
    
    Args:
        entry: os.DirEntry 对象
        show_hidden: 是否显示隐藏文件
        
    Returns:
        是否应该显示
    """
    return get_file_filter().should_show(entry, show_hidden)


def is_system_protected(entry) -> bool:
    """
    便捷函数：检查文件/目录是否受系统保护
    
    Args:
        entry: os.DirEntry 对象或文件路径
        
    Returns:
        是否受系统保护
    """
    return get_file_filter().is_system_protected(entry)


def get_scan_excludes() -> Tuple[bool, List[str]]:
    """
    便捷函数：获取扫描排除配置
    
    Returns:
        (hide_protected, custom_paths)
    """
    return get_file_filter().get_scan_excludes()
