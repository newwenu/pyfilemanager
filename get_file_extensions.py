#!/usr/bin/env python3
"""
获取系统中所有已注册的文件后缀以及有默认打开方式的后缀
增强版本：更全面的扩展名提取和分类
"""

import winreg
import os
import ctypes
from pathlib import Path
from collections import defaultdict


def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_registered_extensions():
    """获取所有已注册的文件扩展名"""
    extensions = set()
    
    try:
        # 方法1: 从HKEY_CLASSES_ROOT获取
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "") as root_key:
            index = 0
            while True:
                try:
                    key_name = winreg.EnumKey(root_key, index)
                    if key_name.startswith('.'):
                        extensions.add(key_name.lower())
                    index += 1
                except OSError:
                    break
        
        # 方法2: 从HKEY_CURRENT_USER\Software\Classes获取（用户特定注册）
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Classes") as user_key:
                index = 0
                while True:
                    try:
                        key_name = winreg.EnumKey(user_key, index)
                        if key_name.startswith('.'):
                            extensions.add(key_name.lower())
                        index += 1
                    except OSError:
                        break
        except OSError:
            pass
        
        # 方法3: 从HKEY_LOCAL_MACHINE\Software\Classes获取（系统级注册）
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\Classes") as machine_key:
                index = 0
                while True:
                    try:
                        key_name = winreg.EnumKey(machine_key, index)
                        if key_name.startswith('.'):
                            extensions.add(key_name.lower())
                        index += 1
                    except OSError:
                        break
        except OSError:
            pass
            
    except Exception as e:
        print(f"读取注册表时出错: {e}")
    
    return sorted(list(extensions))


def get_extension_info(ext, root_key):
    """获取扩展名的详细信息"""
    info = {
        'prog_id': None,
        'program_path': None,
        'program_name': None,
        'description': None,
        'has_open_command': False
    }
    
    try:
        # 获取ProgID
        with winreg.OpenKey(root_key, ext) as ext_key:
            try:
                prog_id, _ = winreg.QueryValueEx(ext_key, "")
                info['prog_id'] = prog_id
            except OSError:
                pass
            
            # 获取描述（如果有）
            try:
                desc, _ = winreg.QueryValueEx(ext_key, "")
                info['description'] = desc
            except OSError:
                pass
            
            # 检查PerceivedType
            try:
                perceived_type, _ = winreg.QueryValueEx(ext_key, "PerceivedType")
                info['perceived_type'] = perceived_type
            except OSError:
                pass
            
            # 检查Content Type
            try:
                content_type, _ = winreg.QueryValueEx(ext_key, "Content Type")
                info['content_type'] = content_type
            except OSError:
                pass
    except OSError:
        return info
    
    # 如果有ProgID，进一步获取程序信息
    if info['prog_id']:
        try:
            with winreg.OpenKey(root_key, info['prog_id']) as prog_key:
                # 获取描述
                try:
                    desc, _ = winreg.QueryValueEx(prog_key, "")
                    if desc and not info['description']:
                        info['description'] = desc
                except OSError:
                    pass
                
                # 检查是否有打开命令
                try:
                    with winreg.OpenKey(prog_key, r"shell\open\command") as cmd_key:
                        command, _ = winreg.QueryValueEx(cmd_key, "")
                        if command:
                            info['has_open_command'] = True
                            # 提取程序路径
                            try:
                                if '"' in command:
                                    program_path = command.split('"')[1]
                                else:
                                    program_path = command.split()[0]
                                
                                info['program_path'] = program_path
                                info['program_name'] = Path(program_path).name
                            except (IndexError, OSError):
                                info['program_name'] = command[:50]  # 限制长度
                except OSError:
                    pass
        except OSError:
            pass
    
    return info

def get_system_supported_extensions():
    """获取Windows系统原生支持的文件扩展名列表"""
    system_extensions = set()
    
    # 1. 从SystemFileAssociations获取系统支持的扩展名
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Classes\SystemFileAssociations") as sys_key:
            # 枚举所有子键（即扩展名）
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(sys_key, i)
                    if subkey_name.startswith('.'):
                        system_extensions.add(subkey_name.lower())
                    i += 1
                except OSError:
                    break
    except OSError:
        pass
    
    # 2. 从HKEY_CLASSES_ROOT获取Windows内置处理程序支持的扩展名
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "") as root_key:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(root_key, i)
                    if subkey_name.startswith('.'):
                        # 检查是否有系统处理程序
                        try:
                            with winreg.OpenKey(root_key, subkey_name) as ext_key:
                                # 检查是否有PerceivedType（感知类型）
                                try:
                                    perceived_type, _ = winreg.QueryValueEx(ext_key, "PerceivedType")
                                    if perceived_type:
                                        system_extensions.add(subkey_name.lower())
                                except OSError:
                                    pass
                        except OSError:
                            pass
                    i += 1
                except OSError:
                    break
    except OSError:
        pass
    
    return sorted(system_extensions)


def get_extensions_with_default_program():
    """获取有默认打开程序的文件扩展名"""
    extensions_with_programs = {}
    all_extensions = get_registered_extensions()
    
    # 检查多个注册表位置
    registry_locations = [
        (winreg.HKEY_CLASSES_ROOT, "HKEY_CLASSES_ROOT"),
        (winreg.HKEY_CURRENT_USER, r"Software\Classes"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Classes")
    ]
    
    # 首先获取所有扩展名的信息
    extension_info = {}
    for ext in all_extensions:
        extension_info[ext] = {
            'has_open_command': False,
            'has_perceived_type': False,
            'has_content_type': False,
            'has_prog_id': False,
            'prog_id': '',
            'description': '',
            'perceived_type': '',
            'content_type': ''
        }
    
    # 收集所有注册表位置的扩展名信息
    for root_key, location_name in registry_locations:
        try:
            with winreg.OpenKey(root_key, "") if location_name == "HKEY_CLASSES_ROOT" else winreg.OpenKey(root_key, location_name.split('\\', 1)[1]) as key:
                for ext in all_extensions:
                    try:
                        info = get_extension_info(ext, key)
                        if info:
                            # 更新扩展名信息
                            if info.get('has_open_command', False):
                                extension_info[ext]['has_open_command'] = True
                            if info.get('perceived_type', ''):
                                extension_info[ext]['has_perceived_type'] = True
                                extension_info[ext]['perceived_type'] = info['perceived_type']
                            if info.get('content_type', ''):
                                extension_info[ext]['has_content_type'] = True
                                extension_info[ext]['content_type'] = info['content_type']
                            if info.get('prog_id', ''):
                                extension_info[ext]['has_prog_id'] = True
                                extension_info[ext]['prog_id'] = info['prog_id']
                            if info.get('description', '') and not extension_info[ext]['description']:
                                extension_info[ext]['description'] = info['description']
                    except OSError:
                        continue
        except OSError:
            continue
    
    # 根据系统实际打开方式判断是否有默认程序
    # 1. 有明确的打开命令
    # 2. 有PerceivedType（感知类型）关联到已知文件类型
    # 3. 有Content Type（MIME类型）关联
    # 4. 有ProgID关联到已知应用程序
    
    # 常见的系统内置文件类型（不需要明确打开命令）
    system_known_types = {
        'text', 'image', 'audio', 'video', 'compressed', 'document', 'system'
    }
    
    for ext, info in extension_info.items():
        has_default_program = False
        
        # 1. 有明确的打开命令
        if info['has_open_command']:
            has_default_program = True
        
        # 2. 有PerceivedType关联到已知文件类型，但需要进一步验证
        elif info['has_perceived_type'] and info['perceived_type'].lower() in system_known_types:
            # 仅仅有PerceivedType不足以确定有默认程序，还需要检查是否有实际的打开命令
            # 检查OpenWithProgids中是否有默认程序
            try:
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"{ext}\\OpenWithProgids") as openwith_key:
                    # OpenWithProgids只是列出可以打开此文件的程序，不是默认程序
                    # 所以不能认为有默认程序
                    pass
            except OSError:
                pass
            
            # 检查是否有shell\open\command
            try:
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ext) as ext_key:
                    try:
                        with winreg.OpenKey(ext_key, "shell\\open\\command") as cmd_key:
                            command, _ = winreg.QueryValueEx(cmd_key, "")
                            if command:
                                has_default_program = True
                    except OSError:
                        pass
            except OSError:
                pass
        
        # 3. 有Content Type（MIME类型）关联，但需要进一步验证
        elif info['has_content_type']:
            # 某些Content Type可能没有直接关联的应用程序
            # 我们需要检查这个Content Type是否有对应的处理程序
            content_type = info['content_type']
            if content_type:
                try:
                    # 检查HKEY_CLASSES_ROOT\MIME\Database\Content Type下是否有这个Content Type的处理程序
                    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"MIME\\Database\\Content Type\\{content_type}") as mime_key:
                        try:
                            # 检查是否有Extension关联，并且Extension是否与当前扩展名匹配
                            extension, _ = winreg.QueryValueEx(mime_key, "Extension")
                            if extension.lower() == ext.lower():
                                has_default_program = True
                        except OSError:
                            # 如果没有Extension，检查CLSID
                            try:
                                winreg.QueryValueEx(mime_key, "CLSID")
                                has_default_program = True
                            except OSError:
                                # 如果都没有，再检查是否有其他处理程序
                                try:
                                    # 尝试打开子键
                                    subkey_count = winreg.QueryInfoKey(mime_key)[0]
                                    if subkey_count > 0:
                                        has_default_program = True
                                except OSError:
                                    pass
                except OSError:
                    # 如果MIME数据库中没有这个Content Type，我们不做假设
                    pass
        
        # 4. 有ProgID关联到已知应用程序
        elif info['has_prog_id'] and info['prog_id']:
            # 检查ProgID是否关联到已知应用程序
            for root_key, location_name in registry_locations:
                try:
                    with winreg.OpenKey(root_key, "") if location_name == "HKEY_CLASSES_ROOT" else winreg.OpenKey(root_key, location_name.split('\\', 1)[1]) as key:
                        try:
                            with winreg.OpenKey(key, info['prog_id']) as prog_key:
                                # 检查是否有shell\open\command
                                try:
                                    with winreg.OpenKey(prog_key, r"shell\open\command") as cmd_key:
                                        command, _ = winreg.QueryValueEx(cmd_key, "")
                                        if command:
                                            has_default_program = True
                                            break
                                except OSError:
                                    pass
                        except OSError:
                            pass
                except OSError:
                    pass
                if has_default_program:
                    break
        
        # 4.1. 检查OpenWithProgids中是否有默认程序
        if not has_default_program:
            try:
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"{ext}\\OpenWithProgids") as openwith_key:
                    # OpenWithProgids只是列出可以打开此文件的程序，不是默认程序
                    # 我们需要检查这些程序是否有默认的打开命令
                    i = 0
                    while True:
                        try:
                            prog_id, _, _ = winreg.EnumValue(openwith_key, i)
                            # 检查这个ProgID是否有打开命令
                            for root_key, location_name in registry_locations:
                                try:
                                    with winreg.OpenKey(root_key, "") if location_name == "HKEY_CLASSES_ROOT" else winreg.OpenKey(root_key, location_name.split('\\', 1)[1]) as key:
                                        try:
                                            with winreg.OpenKey(key, prog_id) as prog_key:
                                                try:
                                                    with winreg.OpenKey(prog_key, r"shell\open\command") as cmd_key:
                                                        command, _ = winreg.QueryValueEx(cmd_key, "")
                                                        if command:
                                                            # 即使有打开命令，OpenWithProgids也不是默认程序
                                                            # 所以不能认为有默认程序
                                                            pass
                                                except OSError:
                                                    pass
                                        except OSError:
                                            pass
                                except OSError:
                                    pass
                            i += 1
                        except OSError:
                            break
            except OSError:
                pass
        
        # 5. 特殊情况：某些扩展名虽然没有上述关联，但Windows知道如何打开
        if not has_default_program:
            # 检查是否是Windows系统内置支持的文件类型
            # 通过检查系统已知文件类型注册表项来判断
            try:
                # 检查系统文件类型关联
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Classes\SystemFileAssociations") as sys_key:
                    try:
                        # 尝试打开扩展名对应的系统文件类型
                        with winreg.OpenKey(sys_key, ext) as ext_sys_key:
                            # 检查是否有处理程序
                            try:
                                with winreg.OpenKey(ext_sys_key, "shell") as shell_key:
                                    # 检查是否有实际的打开命令
                                    try:
                                        with winreg.OpenKey(shell_key, "open\\command") as cmd_key:
                                            command, _ = winreg.QueryValueEx(cmd_key, "")
                                            if command:
                                                has_default_program = True
                                    except OSError:
                                        # 没有明确的打开命令，不能认为有默认程序
                                        pass
                            except OSError:
                                # 没有shell命令，不能认为有默认程序
                                pass
                    except OSError:
                        pass
            except OSError:
                pass
        
        # 6. 最后检查：检查HKEY_CLASSES_ROOT\SystemFileAssociations下的扩展名
        if not has_default_program:
            try:
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"SystemFileAssociations") as sys_key:
                    try:
                        with winreg.OpenKey(sys_key, ext) as ext_sys_key:
                            # 检查是否有PerceivedType
                            try:
                                perceived_type, _ = winreg.QueryValueEx(ext_sys_key, "PerceivedType")
                                if perceived_type and perceived_type.lower() in system_known_types:
                                    # 检查是否有实际的打开命令
                                    try:
                                        with winreg.OpenKey(ext_sys_key, "shell\\open\\command") as cmd_key:
                                            command, _ = winreg.QueryValueEx(cmd_key, "")
                                            if command:
                                                has_default_program = True
                                    except OSError:
                                        # 没有明确的打开命令，不能认为有默认程序
                                        pass
                            except OSError:
                                # 没有PerceivedType，不能认为有默认程序
                                pass
                    except OSError:
                        pass
            except OSError:
                pass
        
        if has_default_program:
            # 获取完整的扩展名信息
            full_info = get_extension_info(ext, winreg.HKEY_CLASSES_ROOT)
            extensions_with_programs[ext] = full_info
    
    return extensions_with_programs


def get_extension_description(ext):
    """获取文件扩展名的描述"""
    registry_locations = [
        (winreg.HKEY_CLASSES_ROOT, "HKEY_CLASSES_ROOT"),
        (winreg.HKEY_CURRENT_USER, r"Software\Classes"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Classes")
    ]
    
    for root_key, location_name in registry_locations:
        try:
            with winreg.OpenKey(root_key, "") if location_name == "HKEY_CLASSES_ROOT" else winreg.OpenKey(root_key, location_name.split('\\', 1)[1]) as key:
                try:
                    with winreg.OpenKey(key, ext) as ext_key:
                        # 首先尝试获取ProgID
                        try:
                            prog_id, _ = winreg.QueryValueEx(ext_key, "")
                            if prog_id:
                                # 尝试从ProgID获取描述
                                try:
                                    with winreg.OpenKey(key, prog_id) as prog_key:
                                        desc, _ = winreg.QueryValueEx(prog_key, "")
                                        if desc:
                                            return desc
                                except OSError:
                                    pass
                        except OSError:
                            pass
                        
                        # 如果没有ProgID描述，尝试直接获取扩展名的描述
                        try:
                            desc, _ = winreg.QueryValueEx(ext_key, "")
                            if desc:
                                return desc
                        except OSError:
                            pass
                except OSError:
                    continue
        except OSError:
            continue
    
    return ""


def save_report(all_extensions, extensions_with_programs, output_file="file_extensions_report.txt"):
    """保存详细的扩展名报告到文件"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("系统文件扩展名报告\n")
            f.write("=" * 80 + "\n\n")
            
            # 统计信息
            f.write(f"已注册扩展名总数: {len(all_extensions)}\n")
            f.write(f"有默认程序的扩展名: {len(extensions_with_programs)}\n")
            f.write(f"无默认程序的扩展名: {len(all_extensions) - len(extensions_with_programs)}\n\n")
            
            # 分类统计
            registered_only = [ext for ext in all_extensions if ext not in extensions_with_programs]
            
            f.write("=" * 80 + "\n")
            f.write("详细分类信息\n")
            f.write("=" * 80 + "\n\n")
            
            # 有默认程序的扩展名
            f.write(f"有默认打开程序的扩展名 ({len(extensions_with_programs)} 个):\n")
            f.write("-" * 60 + "\n")
            
            # 按程序分类
            program_categories = defaultdict(list)
            for ext, info in extensions_with_programs.items():
                prog_name = info.get('program_name', 'Unknown')
                program_categories[prog_name].append((ext, info))
            
            for prog_name in sorted(program_categories.keys(), key=lambda x: x if x else ""):
                exts = program_categories[prog_name]
                f.write(f"\n{prog_name} ({len(exts)} 个):\n")
                for ext, info in sorted(exts, key=lambda x: x[0] if x[0] else ""):
                    desc = get_extension_description(ext)
                    f.write(f"  ✓ {ext:<10} {desc}\n")
            
            # 只有注册但无默认程序的扩展名
            f.write(f"\n\n仅注册但无默认程序的扩展名 ({len(registered_only)} 个):\n")
            f.write("-" * 60 + "\n")
            
            # 按字母顺序分组显示
            registered_only.sort()
            current_letter = ""
            for ext in registered_only:
                first_letter = ext[1].upper()  # 去掉点后的第一个字母
                if first_letter != current_letter:
                    current_letter = first_letter
                    f.write(f"\n{current_letter}:\n")
                desc = get_extension_description(ext)
                f.write(f"  ✗ {ext:<10} {desc}\n")
            
            # 统计图表
            f.write(f"\n\n统计图表:\n")
            f.write("-" * 40 + "\n")
            total_with_programs = len(extensions_with_programs)
            total_registered_only = len(registered_only)
            total_all = len(all_extensions)
            
            if total_all > 0:
                with_programs_pct = (total_with_programs / total_all) * 100
                registered_only_pct = (total_registered_only / total_all) * 100
                
                f.write(f"有默认程序: {'█' * int(with_programs_pct / 2)} {with_programs_pct:.1f}%\n")
                f.write(f"仅注册:     {'█' * int(registered_only_pct / 2)} {registered_only_pct:.1f}%\n")
            
            f.write(f"\n报告生成时间: {os.path.basename(output_file)}\n")
            f.write(f"生成时间: {os.path.abspath(output_file)}\n")
            
        return True
    except Exception as e:
        print(f"保存报告时出错: {e}")
        return False

def main():
    """主函数 - 直接保存结果到文件"""
    # 获取所有已注册的扩展名
    all_extensions = get_registered_extensions()
    
    # 获取有默认程序的扩展名
    extensions_with_programs = get_extensions_with_default_program()
    
    # 直接保存到文件
    output_file = "file_extensions_report.txt"
    save_report(all_extensions, extensions_with_programs, output_file)


if __name__ == "__main__":
    main()