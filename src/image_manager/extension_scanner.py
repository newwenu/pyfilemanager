"""
扩展名扫描器模块
负责扫描系统中所有已注册的文件扩展名
"""
import winreg
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .extension_collector import ExtensionInfo


class ExtensionScanner:
    """扩展名扫描器"""
    
    def __init__(self):
        self.registry_locations = [
            (winreg.HKEY_CLASSES_ROOT, "HKEY_CLASSES_ROOT"),
            (winreg.HKEY_CURRENT_USER, r"Software\Classes"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Classes")
        ]
    
    def get_all_registered_extensions(self) -> Dict[str, ExtensionInfo]:
        """获取所有已注册的文件扩展名"""
        extensions = {}
        
        # 从各个注册表位置获取扩展名
        for root_key, location_name in self.registry_locations:
            try:
                key_path = "" if location_name == "HKEY_CLASSES_ROOT" else location_name.split('\\', 1)[1]
                with winreg.OpenKey(root_key, key_path) as key:
                    index = 0
                    while True:
                        try:
                            key_name = winreg.EnumKey(key, index)
                            if key_name.startswith('.'):
                                ext_lower = key_name.lower()
                                # 如果扩展名尚未处理，则获取其信息
                                if ext_lower not in extensions:
                                    extensions[ext_lower] = self._get_extension_info(key_name)
                            index += 1
                        except OSError:
                            break
            except OSError:
                continue
                
        return extensions
    
    def _get_extension_info(self, extension: str) -> ExtensionInfo:
        """获取扩展名的详细信息"""
        info = ExtensionInfo(extension=extension)
        
        # 从各个注册表位置获取扩展名信息
        for root_key, location_name in self.registry_locations:
            try:
                key_path = "" if location_name == "HKEY_CLASSES_ROOT" else location_name.split('\\', 1)[1]
                with winreg.OpenKey(root_key, key_path) as key:
                    try:
                        with winreg.OpenKey(key, extension) as ext_key:
                            # 获取ProgID
                            try:
                                prog_id, _ = winreg.QueryValueEx(ext_key, "")
                                if prog_id and not info.prog_id:
                                    info.prog_id = prog_id
                            except OSError:
                                pass
                            
                            # 获取描述
                            try:
                                desc, _ = winreg.QueryValueEx(ext_key, "")
                                if desc and not info.description:
                                    info.description = desc
                            except OSError:
                                pass
                            
                            # 获取PerceivedType
                            try:
                                perceived_type, _ = winreg.QueryValueEx(ext_key, "PerceivedType")
                                if perceived_type and not info.perceived_type:
                                    info.perceived_type = perceived_type
                            except OSError:
                                pass
                            
                            # 获取Content Type
                            try:
                                content_type, _ = winreg.QueryValueEx(ext_key, "Content Type")
                                if content_type and not info.content_type:
                                    info.content_type = content_type
                            except OSError:
                                pass
                    except OSError:
                        pass
            except OSError:
                continue
        
        # 如果有ProgID，进一步获取程序信息
        if info.prog_id:
            self._get_prog_id_info(info)
        
        # 检查是否有默认打开程序
        info.has_default_program = self._has_default_program(info.extension)
        
        return info
    
    def _get_prog_id_info(self, info: ExtensionInfo):
        """从ProgID获取程序信息"""
        for root_key, location_name in self.registry_locations:
            try:
                key_path = "" if location_name == "HKEY_CLASSES_ROOT" else location_name.split('\\', 1)[1]
                with winreg.OpenKey(root_key, key_path) as key:
                    try:
                        with winreg.OpenKey(key, info.prog_id) as prog_key:
                            # 获取描述
                            try:
                                desc, _ = winreg.QueryValueEx(prog_key, "")
                                if desc and not info.description:
                                    info.description = desc
                            except OSError:
                                pass
                            
                            # 检查是否有打开命令
                            try:
                                with winreg.OpenKey(prog_key, r"shell\open\command") as cmd_key:
                                    command, _ = winreg.QueryValueEx(cmd_key, "")
                                    if command:
                                        # 提取程序路径
                                        try:
                                            if '"' in command:
                                                program_path = command.split('"')[1]
                                            else:
                                                program_path = command.split()[0]
                                            
                                            info.program_path = program_path
                                            info.program_name = Path(program_path).name
                                        except (IndexError, OSError):
                                            info.program_name = command[:50]  # 限制长度
                            except OSError:
                                pass
                    except OSError:
                        pass
            except OSError:
                continue
    
    def _has_default_program(self, extension: str) -> bool:
        """检查扩展名是否有默认打开程序"""
        # 1. 检查是否有明确的打开命令
        for root_key, location_name in self.registry_locations:
            try:
                key_path = "" if location_name == "HKEY_CLASSES_ROOT" else location_name.split('\\', 1)[1]
                with winreg.OpenKey(root_key, key_path) as key:
                    try:
                        with winreg.OpenKey(key, extension) as ext_key:
                            try:
                                with winreg.OpenKey(ext_key, r"shell\open\command") as cmd_key:
                                    command, _ = winreg.QueryValueEx(cmd_key, "")
                                    if command:
                                        return True
                            except OSError:
                                pass
                    except OSError:
                        pass
            except OSError:
                continue
        
        # 2. 检查ProgID是否有打开命令
        for root_key, location_name in self.registry_locations:
            try:
                key_path = "" if location_name == "HKEY_CLASSES_ROOT" else location_name.split('\\', 1)[1]
                with winreg.OpenKey(root_key, key_path) as key:
                    try:
                        with winreg.OpenKey(key, extension) as ext_key:
                            try:
                                prog_id, _ = winreg.QueryValueEx(ext_key, "")
                                if prog_id:
                                    try:
                                        with winreg.OpenKey(key, prog_id) as prog_key:
                                            try:
                                                with winreg.OpenKey(prog_key, r"shell\open\command") as cmd_key:
                                                    command, _ = winreg.QueryValueEx(cmd_key, "")
                                                    if command:
                                                        return True
                                            except OSError:
                                                pass
                                    except OSError:
                                        pass
                            except OSError:
                                pass
                    except OSError:
                        pass
            except OSError:
                continue
        
        # 3. 检查系统文件类型关联
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Classes\SystemFileAssociations") as sys_key:
                try:
                    with winreg.OpenKey(sys_key, extension) as ext_sys_key:
                        try:
                            with winreg.OpenKey(ext_sys_key, "shell\\open\\command") as cmd_key:
                                command, _ = winreg.QueryValueEx(cmd_key, "")
                                if command:
                                    return True
                        except OSError:
                            pass
                except OSError:
                    pass
        except OSError:
            pass
        
        return False
    
    def scan_system_extensions(self) -> Dict[str, ExtensionInfo]:
        """扫描系统中的所有扩展名"""
        return self.get_all_registered_extensions()