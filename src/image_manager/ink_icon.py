import os
import pythoncom
from win32com.shell import shell, shellcon
from PIL import Image
import win32ui
import win32gui


def get_shortcut_icon(shortcut_path, icon_size=32):
    """
    获取快捷方式(.lnk文件)的图标
    :param shortcut_path: 快捷方式的路径
    :param icon_size: 图标大小，默认32x32
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
            icon_index = icon_location[1]
        else:  # 否则使用目标文件的图标
            target_path = shortcut.GetPath(0)[0]
            icon_path = target_path
            icon_index = 0
        
        # 提取图标
        large, small = win32gui.ExtractIconEx(icon_path, icon_index, 1)
        if small:
            win32gui.DestroyIcon(large[0])
            hicon = small[0]
        elif large:
            win32gui.DestroyIcon(small[0])
            hicon = large[0]
        else:
            return None
        
        # 将图标转换为图片
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, icon_size, icon_size)
        hdc = hdc.CreateCompatibleDC()
        hdc.SelectObject(hbmp)
        hdc.DrawIcon((0, 0), hicon)
        win32gui.DestroyIcon(hicon)
        
        # 保存图标为图片文件
        bmpinfo = hbmp.GetInfo()
        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)
        
        # 保存图标到临时目录
        temp_icon_dir = os.path.join("media", "shortcut_icons")
        os.makedirs(temp_icon_dir, exist_ok=True)
        icon_filename = os.path.basename(shortcut_path) + f"_{icon_size}.png"
        icon_output_path = os.path.join(temp_icon_dir, icon_filename)
        img.save(icon_output_path)
        return icon_output_path
    except Exception as e:
        print(f"提取快捷方式图标失败: {e}")
        return None


def get_shortcut_icon_pixmap(shortcut_path, icon_size=32):
    """
    获取快捷方式图标并返回QPixmap对象
    :param shortcut_path: 快捷方式的路径
    :param icon_size: 图标大小
    :return: QPixmap对象或None
    """
    from PySide6.QtGui import QPixmap
    icon_path = get_shortcut_icon(shortcut_path, icon_size)
    if icon_path and os.path.exists(icon_path):
        return QPixmap(icon_path)
    return None
