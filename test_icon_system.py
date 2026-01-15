#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图标系统测试脚本
用于测试新的图标配置系统是否正常工作
"""

import sys
import os
import time
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# 初始化Qt应用程序
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication

# 创建全局Qt应用程序实例
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

def test_icon_config_manager():
    """测试图标配置管理器"""
    print("=" * 50)
    print("测试图标配置管理器")
    print("=" * 50)
    
    try:
        from src.image_manager.icon_config_manager import IconConfigManager
        
        # 创建配置管理器实例
        config_manager = IconConfigManager()
        
        # 测试获取活动主题
        active_theme = config_manager.active_theme
        print(f"活动主题: {active_theme}")
        
        # 测试获取所有主题
        themes = config_manager.get_available_themes()
        print(f"可用主题: {themes}")
        
        # 测试获取图标映射规则
        mappings = config_manager.icon_mappings
        print(f"图标映射数量: {len(mappings)}")
        
        # 测试获取文件类型
        file_type = config_manager.get_icon_for_file("test.txt")
        print(f"test.txt 的文件类型: {file_type}")
        
        file_type = config_manager.get_icon_for_file("test.exe")
        print(f"test.exe 的文件类型: {file_type}")
        
        file_type = config_manager.get_icon_for_file("unknown.xyz")
        print(f"unknown.xyz 的文件类型: {file_type}")
        
        # 测试获取图标文件路径
        icon_path = config_manager.get_icon_path("text")
        print(f"text 类型的图标路径: {icon_path}")
        
        # 测试获取字符图标
        char_icon = config_manager.get_char_icon("text")
        print(f"text 类型的字符图标: {char_icon}")
        
        print("\n✅ 图标配置管理器测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 图标配置管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_icon_manager():
    """测试图标管理器"""
    print("=" * 50)
    print("测试图标管理器")
    print("=" * 50)
    
    try:
        from src.image_manager.icon_manager_new import IconManager
        
        # 创建图标管理器实例
        icon_manager = IconManager()
        
        # 测试获取图标缓存
        icons = icon_manager.icon_cache
        print(f"缓存中的图标数量: {len(icons)}")
        
        # 测试获取图标
        icon = icon_manager.get_icon("text")
        print(f"text 图标: {icon}")
        
        # 测试获取图标路径
        icon_path = icon_manager.config_manager.get_icon_path("text")
        print(f"text 图标路径: {icon_path}")
        
        # 测试切换主题
        print("尝试切换到 dark 主题...")
        icon_manager.set_active_theme("dark")
        
        # 测试重新加载图标
        print("重新加载图标...")
        icon_manager.refresh_cache()
        
        print("\n✅ 图标管理器测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 图标管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_icon_adapter():
    """测试文件图标适配器"""
    print("=" * 50)
    print("测试文件图标适配器")
    print("=" * 50)
    
    try:
        from src.utils.file_icon_adapter import get_file_type, get_icon_char, get_file_properties
        
        # 测试获取文件类型
        file_type = get_file_type("test.txt")
        print(f"test.txt 的文件类型: {file_type}")
        
        file_type = get_file_type("test.exe")
        print(f"test.exe 的文件类型: {file_type}")
        
        # 测试获取字符图标
        char_icon = get_icon_char("text")
        print(f"text 类型的字符图标: {char_icon}")
        
        # 测试获取文件属性
        props = get_file_properties(__file__)  # 使用当前文件而不是不存在的test.txt
        print(f"当前文件的属性: {props}")
        
        print("\n✅ 文件图标适配器测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 文件图标适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_icon_manager_factory():
    """测试图标管理器工厂"""
    print("=" * 50)
    print("测试图标管理器工厂")
    print("=" * 50)
    
    try:
        from image_manager.icon_manager_factory import (
            get_icon_manager, 
            get_config_manager, 
            switch_to_new_icon_system,
            switch_to_legacy_icon_system,
            is_using_new_icon_system
        )
        
        # 测试获取当前系统
        current_system = "new" if is_using_new_icon_system() else "legacy"
        print(f"当前图标系统: {current_system}")
        
        # 测试切换到新系统
        print("切换到新图标系统...")
        switch_to_new_icon_system()
        
        # 测试获取图标管理器
        icon_manager = get_icon_manager()
        print(f"图标管理器类型: {type(icon_manager).__name__}")
        
        # 测试获取配置管理器
        config_manager = get_config_manager()
        print(f"配置管理器类型: {type(config_manager).__name__}")
        
        print("\n✅ 图标管理器工厂测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 图标管理器工厂测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """集成测试"""
    print("=" * 50)
    print("集成测试")
    print("=" * 50)
    
    try:
        from src.image_manager.icon_manager_factory import get_icon_manager
        from src.utils.file_icon_adapter import get_file_type, get_icon_char, get_file_properties
        
        # 获取图标管理器
        icon_manager = get_icon_manager()
        
        # 使用当前文件进行测试
        test_file = __file__
        
        # 获取文件类型
        file_type = get_file_type(test_file)
        
        # 获取字符图标
        char_icon = get_icon_char(file_type)
        
        # 获取文件属性
        props = get_file_properties(test_file)
        
        print(f"{test_file}: 类型={file_type}, 字符图标={char_icon}")
        print(f"  文件属性: {props}")
        
        # 获取图标
        icon = icon_manager.get_icon(file_type)
        print(f"  图标: {icon}")
        
        print("\n✅ 集成测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始图标系统测试")
    print(f"工作目录: {os.getcwd()}")
    print(f"Python路径: {sys.path[0]}")
    
    # 运行所有测试
    tests = [
        test_icon_config_manager,
        test_icon_manager,
        test_file_icon_adapter,
        test_icon_manager_factory,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 50)
    
    if passed == total:
        print("🎉 所有测试通过！新图标系统工作正常。")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())