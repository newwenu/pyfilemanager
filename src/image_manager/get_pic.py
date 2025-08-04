import urllib.request
from urllib.error import URLError, HTTPError
import os
import hashlib  # 新增：用于计算文件哈希值
import configparser
from utils.logging_config import get_logger
logger = get_logger(__name__)

def get_webp(url=None):
    
    save_path = os.path.join("media","webpic")
    if url is None:
        ini_path = os.path.join("userdata","config","url.ini")
        config = configparser.ConfigParser()
        if not os.path.exists(ini_path):
            os.makedirs(os.path.dirname(ini_path))
        config.read(ini_path)
        url = config.get('pic_url', 'url1')
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            content = r.read()
            status_code = r.status
    except (URLError, HTTPError) as e:
        print(f"请求失败: {e.reason}")
        return ""
    print(f"请求状态码：{status_code}")
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    # # 第一步：获取当前最大序号（用于生成新文件名）
    # existing_files = [f for f in os.listdir(save_path) if f.startswith('background') and f.split('.')[-1].lower() in ALLOWED_TYPES]
    # max_num = 0
    # for file in existing_files:
    #     try:
    #         # 从文件名中提取数字（例如从"background3.png"提取3）
    #         num = int(file.split('background')[1].split(f'.{image_type}')[0])
    #         if num > max_num:
    #             max_num = num
    #     except (ValueError, IndexError):  # 跳过格式错误的文件（如"background-abc.png"）
    #         continue
    # new_num = max_num + 1

    # # 第二步：计算新图片的哈希值（用于去重）
    # # 修改哈希计算部分
    # new_image_hash = hashlib.md5(content).hexdigest()

    # # 第三步：检查是否已有相同内容的图片
    # is_duplicate = False
    # for file in existing_files:
    #     with open(os.path.join(save_path,file), 'rb') as f:  # 以二进制模式读取已保存的图片
    #         if hashlib.md5(f.read()).hexdigest() == new_image_hash:
    #             is_duplicate = True
    #             break
    # 新增：检测实际图片格式
    from imghdr import what  # 内置图片类型检测库
    image_type = None
    try:
        # 首选方案：通过文件头检测
        image_type = what(None, h=content)
        # 备选通过Content-Type判断
        if not image_type and'image/' in content_type:
            content_type = r.headers.get('Content-Type', '')
            image_type = content_type.split('/')[-1].lower()
        
        # 特殊处理JPEG扩展名
        if image_type == 'jpeg':
            image_type = 'jpg'
            
    except Exception as e:
        logger.error(f"图片格式检测失败: {e}")
        image_type='webp'
    
    # 支持格式白名单
    ALLOWED_TYPES = {'jpeg', 'png', 'webp', 'bmp','jpg'}
    if not image_type or image_type not in ALLOWED_TYPES:
        logger.warning(f"不支持的图片格式: {image_type}")
        return ""

    # 修改文件名生成逻辑
    existing_files = [f for f in os.listdir(save_path) 
                     if f.startswith('background') 
                     and f.split('.')[-1].lower() in ALLOWED_TYPES]  # 扩展格式判断
    max_num = 0
    for file in existing_files:
        try:
            # 从文件名中提取数字（例如从"background3.png"提取3）
            num = int(file.split('background')[1].split(f'.{image_type}')[0])
            if num > max_num:
                max_num = num
        except (ValueError, IndexError):  # 跳过格式错误的文件（如"background-abc.png"）
            continue
    new_num = max_num + 1

    # 第二步：计算新图片的哈希值（用于去重）
    # 修改哈希计算部分
    new_image_hash = hashlib.md5(content).hexdigest()

    # 第三步：检查是否已有相同内容的图片
    is_duplicate = False
    for file in existing_files:
        with open(os.path.join(save_path,file), 'rb') as f:  # 以二进制模式读取已保存的图片
            if hashlib.md5(f.read()).hexdigest() == new_image_hash:
                is_duplicate = True
                break
    
    return save_image(content,image_type,is_duplicate,new_num,save_path)

    
# def save_webp(content,is_duplicate,new_num,save_path):
#     # 修改保存部分
#     if not is_duplicate:
#         save_path = os.path.join(save_path, f"background{new_num}.webp")
#         with open(save_path, "wb") as f:
#             f.write(content)  # 使用从urllib获取的内容
#         print(f"新图片已保存为：{save_path}")
#     return save_path

def save_image(content, img_type, is_duplicate, new_num, save_path):
    """通用图片保存函数"""
    if not is_duplicate:
        # 格式校验
        valid_types = {
            'jpg': b'\xff\xd8',
            'png': b'\x89PNG',
            'webp': b'RIFF',
            'bmp': b'BM'
        }
        # print(img_type)
        # print(content[:10])
        # if img_type in valid_types and not content.startswith(valid_types[img_type]) :
        #     logger.error("文件头与格式不匹配",img_type)
        #     return ""
        
        filename = f"background{new_num}.{img_type}"
        save_path = os.path.join(save_path, filename)
        with open(save_path, "wb") as f:
            f.write(content)
        print(f"新图片已保存为：{save_path}")
    return save_path

if __name__ == "__main__":
    get_webp()