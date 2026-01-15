"""
扩展名集合初始化脚本
在应用程序启动时初始化扩展名集合
"""
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.image_manager.extension_manager import ExtensionManager


def initialize_extensions():
    """初始化扩展名集合"""
    print("正在初始化扩展名集合...")
    
    # 检查扩展名集合文件是否存在
    extension_config_path = "userdata/file-icon-type/extensions_collection.json"
    if os.path.exists(extension_config_path):
        print("扩展名集合文件已存在，跳过初始化")
        return True
    
    try:
        # 创建扩展名管理器
        extension_manager = ExtensionManager(extension_config_path)
        
        # 扫描并更新扩展名
        stats = extension_manager.scan_and_save_extensions()
        success = stats["total_saved"] > 0
        
        if success:
            print(f"扩展名集合初始化成功，共 {stats['total_saved']} 个扩展名")
        else:
            print("扩展名集合初始化失败")
            
        return success
    except Exception as e:
        print(f"初始化扩展名集合时出错: {e}")
        return False


def refresh_extensions_if_needed():
    """如果需要，刷新扩展名集合"""
    try:
        # 直接创建扩展名管理器
        extension_config_path = "userdata/file-icon-type/extensions_collection.json"
        extension_manager = ExtensionManager(extension_config_path)
        
        # 检查扩展名数量
        extensions_count = extension_manager.get_extensions_count()
        print(f"当前扩展名集合中共有 {extensions_count} 个扩展名")
        
        # 如果扩展名数量为0，尝试刷新
        if extensions_count == 0:
            print("扩展名集合为空，尝试刷新...")
            stats = extension_manager.scan_and_save_extensions()
            success = stats["total_saved"] > 0
            if success:
                print(f"扩展名集合刷新成功，共 {stats['total_saved']} 个扩展名")
            else:
                print("扩展名集合刷新失败")
            return success
        
        return True
    except Exception as e:
        print(f"刷新扩展名集合时出错: {e}")
        return False


if __name__ == "__main__":
    # 确保目录存在
    os.makedirs(os.path.dirname("userdata/file-icon-type/"), exist_ok=True)
    
    # 初始化扩展名集合
    initialize_extensions()
    
    # 刷新扩展名集合（如果需要）
    refresh_extensions_if_needed()