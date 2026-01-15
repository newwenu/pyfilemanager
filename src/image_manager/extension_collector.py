"""
扩展名收集器模块
负责收集系统中所有已注册的文件扩展名并保存到配置文件中
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExtensionInfo:
    """扩展名信息"""
    extension: str
    description: str = ""
    perceived_type: str = ""
    content_type: str = ""
    prog_id: str = ""
    has_default_program: bool = False
    program_path: str = ""
    program_name: str = ""
    last_modified: str = ""


class ExtensionCollector:
    """扩展名收集器"""
    
    def __init__(self, config_path: str = "userdata/file-icon-type/extensions_collection.json"):
        self.config_path = config_path
        self.extensions: Dict[str, ExtensionInfo] = {}
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        config_dir = os.path.dirname(self.config_path)
        Path(config_dir).mkdir(parents=True, exist_ok=True)
    
    def load_extensions(self) -> bool:
        """从配置文件加载扩展名信息"""
        try:
            if not os.path.exists(self.config_path):
                return False
                
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self.extensions = {}
            
            # 处理新的简化格式（扩展名列表）
            if isinstance(data.get("extensions"), list):
                for ext in data.get("extensions", []):
                    # 确保扩展名以点开头
                    if not ext.startswith('.'):
                        ext = f".{ext}"
                    self.extensions[ext.lower()] = ExtensionInfo(extension=ext.lower())
            # 处理旧的详细格式（兼容性）
            elif isinstance(data.get("extensions"), dict):
                for ext, info in data.get("extensions", {}).items():
                    self.extensions[ext] = ExtensionInfo(**info)
                
            return True
        except Exception as e:
            print(f"加载扩展名配置失败: {e}")
            return False
    
    def save_extensions(self) -> bool:
        """保存扩展名信息到配置文件"""
        try:
            # 只保存扩展名列表，不包含详细信息
            extensions_list = list(self.extensions.keys())
            
            data = {
                "last_updated": datetime.now().isoformat(),
                "total_count": len(extensions_list),
                "extensions": extensions_list
            }
            
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            return True
        except Exception as e:
            print(f"保存扩展名配置失败: {e}")
            return False
    
    def add_extension(self, extension_info: ExtensionInfo) -> bool:
        """添加扩展名信息"""
        if not extension_info.extension:
            return False
            
        # 确保扩展名以点开头
        ext = extension_info.extension
        if not ext.startswith('.'):
            ext = f".{ext}"
            
        # 添加时间戳
        if not extension_info.last_modified:
            extension_info.last_modified = datetime.now().isoformat()
            
        self.extensions[ext.lower()] = extension_info
        return True
    
    def remove_extension(self, extension: str) -> bool:
        """删除扩展名信息"""
        ext = extension.lower()
        if not ext.startswith('.'):
            ext = f".{ext}"
            
        if ext in self.extensions:
            del self.extensions[ext]
            return True
        return False
    
    def get_extension(self, extension: str) -> Optional[ExtensionInfo]:
        """获取扩展名信息"""
        ext = extension.lower()
        if not ext.startswith('.'):
            ext = f".{ext}"
            
        return self.extensions.get(ext)
    
    def get_all_extensions(self) -> List[str]:
        """获取所有扩展名列表"""
        return list(self.extensions.keys())
    
    def get_extensions_with_default_program(self) -> List[str]:
        """获取有默认程序的扩展名列表"""
        return [ext for ext, info in self.extensions.items() if info.has_default_program]
    
    def get_extensions_by_type(self, perceived_type: str) -> List[str]:
        """根据感知类型获取扩展名列表"""
        return [ext for ext, info in self.extensions.items() 
                if info.perceived_type.lower() == perceived_type.lower()]
    
    def merge_from_system_scan(self, system_extensions: Dict[str, dict]) -> int:
        """从系统扫描结果合并扩展名信息"""
        added_count = 0
        
        for ext, info in system_extensions.items():
            # 确保扩展名以点开头
            if not ext.startswith('.'):
                ext = f".{ext}"
                
            ext_lower = ext.lower()
            
            # 如果扩展名不存在或者信息更完整，则添加/更新
            if ext_lower not in self.extensions or info.get('has_open_command', False):
                extension_info = ExtensionInfo(
                    extension=ext_lower,
                    description=info.get('description', ''),
                    perceived_type=info.get('perceived_type', ''),
                    content_type=info.get('content_type', ''),
                    prog_id=info.get('prog_id', ''),
                    has_default_program=info.get('has_open_command', False),
                    program_path=info.get('program_path', ''),
                    program_name=info.get('program_name', ''),
                    last_modified=datetime.now().isoformat()
                )
                
                self.add_extension(extension_info)
                added_count += 1
                
        return added_count
    
    def get_statistics(self) -> Dict[str, int]:
        """获取扩展名统计信息"""
        stats = {
            "total": len(self.extensions),
            "with_default_program": len(self.get_extensions_with_default_program()),
            "by_type": {}
        }
        
        # 按感知类型统计
        type_counts = {}
        for info in self.extensions.values():
            ptype = info.perceived_type.lower() if info.perceived_type else "unknown"
            type_counts[ptype] = type_counts.get(ptype, 0) + 1
            
        stats["by_type"] = type_counts
        return stats