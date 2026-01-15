"""
扩展名管理器模块
整合扩展名扫描和收集功能
"""
import os
from typing import Dict, List, Optional
from .extension_scanner import ExtensionScanner
from .extension_collector import ExtensionCollector, ExtensionInfo


class ExtensionManager:
    """扩展名管理器"""
    
    def __init__(self, config_path: str = "userdata/file-icon-type/extensions_collection.json"):
        self.scanner = ExtensionScanner()
        self.collector = ExtensionCollector(config_path)
        
        # 尝试加载已保存的扩展名
        self.collector.load_extensions()
    
    def scan_and_save_extensions(self, force_update: bool = False) -> Dict[str, int]:
        """扫描系统扩展名并保存到配置文件
        
        Args:
            force_update: 是否强制更新所有扩展名信息
            
        Returns:
            统计信息字典
        """
        # 扫描系统扩展名
        system_extensions = self.scanner.scan_system_extensions()
        
        # 合并到收集器
        added_count = 0
        updated_count = 0
        
        for ext, info in system_extensions.items():
            existing_info = self.collector.get_extension(ext)
            
            if existing_info is None:
                # 新扩展名
                self.collector.add_extension(info)
                added_count += 1
            elif force_update or (info.has_default_program and not existing_info.has_default_program):
                # 更新扩展名信息（强制更新或新信息更完整）
                self.collector.add_extension(info)
                updated_count += 1
        
        # 保存到文件
        self.collector.save_extensions()
        
        # 获取统计信息
        stats = self.collector.get_statistics()
        
        return {
            "total_scanned": len(system_extensions),
            "total_saved": stats["total"],
            "added": added_count,
            "updated": updated_count,
            "with_default_program": stats["with_default_program"],
            "by_type": stats["by_type"]
        }
    
    def get_all_extensions(self) -> List[str]:
        """获取所有已保存的扩展名"""
        return self.collector.get_all_extensions()
    
    def get_extensions_with_default_program(self) -> List[str]:
        """获取有默认程序的扩展名"""
        return self.collector.get_extensions_with_default_program()
    
    def get_extension_info(self, extension: str) -> Optional[ExtensionInfo]:
        """获取特定扩展名的信息"""
        return self.collector.get_extension(extension)
    
    def get_extensions_by_type(self, perceived_type: str) -> List[str]:
        """根据感知类型获取扩展名"""
        return self.collector.get_extensions_by_type(perceived_type)
    
    def get_statistics(self) -> Dict[str, int]:
        """获取扩展名统计信息"""
        return self.collector.get_statistics()
    
    def is_extension_registered(self, extension: str) -> bool:
        """检查扩展名是否已注册"""
        return self.collector.get_extension(extension) is not None
    
    def get_extensions_count(self) -> int:
        """获取已保存的扩展名数量"""
        return len(self.collector.extensions)
    
    def refresh_from_system(self) -> Dict[str, int]:
        """从系统刷新扩展名信息（强制更新所有）"""
        return self.scan_and_save_extensions(force_update=True)