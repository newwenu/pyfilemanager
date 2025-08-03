import urllib.request
from urllib.error import URLError, HTTPError
import os
import hashlib  # 新增：用于计算文件哈希值
import configparser


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
    # 第一步：获取当前最大序号（用于生成新文件名）
    existing_files = [f for f in os.listdir(save_path) if f.startswith('background') and f.endswith('.webp')]
    max_num = 0
    for file in existing_files:
        try:
            # 从文件名中提取数字（例如从"background3.png"提取3）
            num = int(file.split('background')[1].split('.webp')[0])
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
    if __name__ == "__main__":
        print(is_duplicate)
        print(new_num)
        print(max_num)
    return save_webp(content,is_duplicate,new_num,save_path)

    
def save_webp(content,is_duplicate,new_num,save_path):
    # 修改保存部分
    if not is_duplicate:
        save_path = os.path.join(save_path, f"background{new_num}.webp")
        with open(save_path, "wb") as f:
            f.write(content)  # 使用从urllib获取的内容
        print(f"新图片已保存为：{save_path}")
    return save_path

if __name__ == "__main__":
    get_webp()