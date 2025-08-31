import os
import pythoncom
from win32com.shell import shell, shellcon
from PIL import Image, ImageSequence  # 导入 ImageSequence 模块
import win32ui
import win32gui

def get_shortcut_icon(shortcut_path, icon_size=None):
    """
    获取快捷方式(.lnk文件)的图标
    :param shortcut_path: 快捷方式的路径
    :param icon_size: 图标大小，如果为None则使用最大可用图标
    :return: 图标路径或None
    """
    try:
        # 解析快捷方式
        shortcut = pythoncom.CoCreateInstance(
            shell.CLSID_ShellLink,
            None,
            pythoncom.CLSCTX_INPROC_SERVER,
            shell.IID_IShellLink
        )
        persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
        persist_file.Load(shortcut_path)
        
        # 解析快捷方式，使用FOF_NO_UI标志避免UI交互
        shortcut.Resolve(0, shellcon.FOF_NO_UI)
        
        # 获取图标位置
        icon_location = shortcut.GetIconLocation()
        if icon_location[0]:  # 如果快捷方式指定了自定义图标
            icon_path = icon_location[0]
            # icon_index = icon_location[1]
        else:  # 否则使用目标文件的图标
            target_path = shortcut.GetPath(0)[0]
            icon_path = target_path
            # icon_index = 0
        print(icon_path)
        # import win32api
        # import win32com

        if icon_path.endswith(".exe"):
            # # win32com
            # # win32gui.ExtractIcon(icon_path, 0)
            # # 提取图标
            # hicon = win32gui.ExtractIcon(0,icon_path, 0)
            # # 转换为 PIL 图像 - 修复句柄转字节数据
            # icon_info = win32gui.GetIconInfo(hicon)
            # hbm_color = icon_info[3]
            # # 通过位图句柄获取尺寸信息
            # bmp = win32gui.GetObject(hbm_color)  # 获取位图结构
            # width = bmp.bmWidth
            # height = bmp.bmHeight
            # bitmap = win32ui.CreateBitmapFromHandle(hbm_color)
            # # width = bitmap.GetWidth()
            # # height = bitmap.
            # bits = bitmap.GetBitmapBits(True)
            # img = Image.frombuffer('RGB', (width, height), bits, 'raw', 'BGR', 0, 1)
            # # 保存图标到项目目录下的temp文件夹
            # temp_icon_dir = os.path.join("temp", "icons")
            # # os.makedirs(temp_icon_dir, exist_ok=True)
            # icon_filename = os.path.basename(shortcut_path) + ".ico"
            # icon_output_path = os.path.join(temp_icon_dir, icon_filename)
            
            # # 保存为ICO格式
            # img.save(icon_output_path, format='ICO')
            # icon_path = icon_output_path
            large, small = win32gui.ExtractIconEx(icon_path, icon_index, 1)
            if large:
                hicon = large[0]
            elif small:
                hicon = small[0]
            else:
                return None
            # 将图标转换为图片
            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            hbmp = win32ui.CreateBitmap()
            # # 使用实际图标大小创建位图
            # hbmp.CreateCompatibleBitmap(hdc, actual_width, actual_height)
            hdc = hdc.CreateCompatibleDC()
            hdc.SelectObject(hbmp)
            hdc.DrawIcon((0, 0), hicon)
            win32gui.DestroyIcon(hicon)
            
            # 修改图标转换和保存部分
            # 保存图标为图片文件
            # bmpinfo = hbmp.GetInfo()
            # bmpstr = hbmp.GetBitmapBits(True)
            
            # 使用RGBA模式处理透明度
            # img = Image.frombuffer(
            #     'RGBA',  # 使用RGBA模式保留透明度
            #     (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            #     bmpstr, 'raw', 'BGRA', 0, 1)  # 使用BGRA格式正确处理透明通道
            
            # # 保存图标到项目目录下的temp文件夹
            # temp_icon_dir = os.path.join("temp", "icons")
            # # os.makedirs(temp_icon_dir, exist_ok=True)
            # icon_filename = os.path.basename(shortcut_path) + ".ico"
            # icon_output_path = os.path.join(temp_icon_dir, icon_filename)
            
            # # 保存为ICO格式
            # img.save(icon_output_path, format='ICO')

        # 提取最大可用图标
        # 尝试提取大图标，如果失败则提取默认大小图标
        # large, small = win32gui.ExtractIconEx(icon_path, icon_index, 1)
        # if large:
        #     print("大图标")
        #     hicon = large[0]
        #     print("size:",win32gui.GetObject(win32gui.GetIconInfo(hicon)[3]).bmWidth)

        #     # 优先使用大图标 
        # elif small:
        #     # 如果没有大图标，使用小图标
        #     print("小图标")
        #     hicon = small[0]
        # else:
        #     return None
        
        # 获取图标信息以确定实际大小
        # icon_info = win32gui.GetIconInfo(hicon)


        # if icon_info:
        #     bitmap_handle = icon_info[3]  # 获取位图句柄
        #     bitmap_info = win32gui.GetObject(bitmap_handle)
        #     actual_width = bitmap_info.bmWidth
        #     actual_height = bitmap_info.bmHeight
        # else:
        #     # 如果无法获取图标信息，使用默认大小
        #     actual_width = actual_height = 32

        # 调试信息
        print(f"请求的图标大小: {icon_size}")
        # print(f"实际图标宽度: {actual_width}")
        # print(f"实际图标高度: {actual_height}")

        # 将图标转换为图片
        # hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        # hbmp = win32ui.CreateBitmap()
        # # 使用实际图标大小创建位图
        # hbmp.CreateCompatibleBitmap(hdc, actual_width, actual_height)
        # hdc = hdc.CreateCompatibleDC()
        # hdc.SelectObject(hbmp)
        # hdc.DrawIcon((0, 0), hicon)
        # win32gui.DestroyIcon(hicon)
        
        # 修改图标转换和保存部分
        # 保存图标为图片文件
        # bmpinfo = hbmp.GetInfo()
        # bmpstr = hbmp.GetBitmapBits(True)
        
        # 使用RGBA模式处理透明度
        # img = Image.frombuffer(
        #     'RGBA',  # 使用RGBA模式保留透明度
        #     (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        #     bmpstr, 'raw', 'BGRA', 0, 1)  # 使用BGRA格式正确处理透明通道
        
        # # 保存图标到项目目录下的temp文件夹
        # temp_icon_dir = os.path.join("temp", "icons")
        # # os.makedirs(temp_icon_dir, exist_ok=True)
        # icon_filename = os.path.basename(shortcut_path) + ".ico"
        # icon_output_path = os.path.join(temp_icon_dir, icon_filename)
        
        # # 保存为ICO格式
        # img.save(icon_output_path, format='ICO')
        
        # 如果指定了图标大小，则从ICO文件中提取特定尺寸的图标
        # if icon_size and icon_size != actual_width:
        if 1:
            # 使用PIL库从ICO文件中提取特定尺寸的图标
            ico_img = Image.open(icon_path)
            # 获取ICO文件中所有可用的尺寸
            available_sizes = []
            try:
                # 使用 ImageSequence.Iterator 遍历所有帧，获取尺寸
                for frame in ImageSequence.Iterator(ico_img):
                    available_sizes.append(frame.size)
            except Exception as e:
                print(f"获取ICO文件尺寸时出错: {e}")
                # 如果无法获取帧数，使用当前图像尺寸
                available_sizes.append(ico_img.size)
            print(f"ICO文件中可用的尺寸: {available_sizes}")
            # 查找最接近指定尺寸的可用尺寸
            closest_size = min(available_sizes, key=lambda s: abs(s[0] - icon_size))
            print(f"最接近指定尺寸的可用尺寸: {closest_size}")
            
            # 重新打开ICO文件，以确保我们在正确的帧上
            # ico_img = Image.open(icon_output_path)
            # 查找并选择最接近指定尺寸的帧
            for frame in ImageSequence.Iterator(ico_img):
                if frame.size == closest_size:
                    ico_img = frame
                    break
            
            # 如果最接近的尺寸与指定尺寸不同，则进行缩放
            if closest_size[0] != icon_size:
                ico_img = ico_img.resize((icon_size, icon_size), Image.LANCZOS)
            
            # 保存为ICO格式
            # ico_img.save(icon_output_path, format='ICO')
        
        return icon_path
    except Exception as e:
        print(f"提取快捷方式图标失败: {e}")
        return None

def get_shortcut_icon_pixmap(shortcut_path, icon_size=None):
    """
    获取快捷方式图标并返回QPixmap对象
    :param shortcut_path: 快捷方式的路径
    :param icon_size: 图标大小
    :return: QPixmap对象或None
    """
    icon_size*=2
    from PySide6.QtGui import QPixmap
    from PySide6.QtCore import Qt
    icon_path = get_shortcut_icon(shortcut_path, icon_size)
    if icon_path and os.path.exists(icon_path):
        pixmap = QPixmap(icon_path)
        # 如果指定了图标大小，则缩放到指定大小
        if icon_size:
            pixmap = pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pixmap
    return None