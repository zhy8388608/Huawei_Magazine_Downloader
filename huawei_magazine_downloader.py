import os
import requests
from urllib.parse import urlparse
import zipfile
import xml.etree.ElementTree as ET

# 定义请求参数
url = "https://magazine-drcn.theme.dbankcloud.cn/servicesupport/theme/getThemeMagazine.do"
params = {
    "sign": "0@11111111222222223333333344444444",
    "themename": "Balance(magazine)",
    "version": "0",
    "phoneType": "PLR-AL00"
}

# 创建根目录
root_dir = "杂志锁屏壁纸"
os.makedirs(root_dir, exist_ok=True)

# 发送请求
response = requests.post(url, data=params)
response.raise_for_status()

# 解析响应
data = response.json()

# 遍历频道列表
for item in data["channellist"]:
    chname, file_url, ver = item["chname"], item["url"], item["ver"]
    
    # 创建频道目录
    channel_dir = os.path.join(root_dir, chname)
    os.makedirs(channel_dir, exist_ok=True)
    
    # 处理文件路径
    file_name = os.path.basename(urlparse(file_url).path)
    file_path = os.path.join(channel_dir, file_name)
    extract_folder = ver.split(".")[2]
    extract_path = os.path.join(channel_dir, extract_folder)
    
    # 下载文件
    print(f"正在下载：{file_path}")
    with requests.get(file_url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    
    # 解压文件
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    
    # 清理zip文件
    os.remove(file_path)
    
    # 解析XML
    xml_path = os.path.join(extract_path, 'layout_balance.xml')
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # 获取icon文件
    icon_file = os.path.join(extract_path, root.find('.//type').get('src'))
    os.remove(icon_file)
    
    # 处理图片信息
    images_info = [
        (img.get('src'), img.get('title'), img.get('content'), img.get('contenturl'))
        for img in root.findall('.//image')
    ]
    
    # 重命名文件
    for src, title, content, contenturl in images_info:
        old_path = os.path.join(extract_path, src)
        ext = os.path.splitext(src)[1]
        new_path = os.path.join(extract_path, f"{title}{ext}")
        
        if os.path.exists(new_path):
            os.remove(new_path)
            
        os.rename(old_path, new_path)
    
    # 写入描述文件
    with open(os.path.join(extract_path, 'desc.txt'), 'w', encoding='utf-8') as f:
        for src, title, content, contenturl in images_info:
            f.write(f"{title}\n{content}\n{contenturl}\n\n")
    
    # 清理XML文件
    os.remove(xml_path)

print("\n**********\n任务完成。\n**********\n")
