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

# 创建根目录用于保存所有频道文件夹
root_dir = "杂志锁屏壁纸"
os.makedirs(root_dir, exist_ok=True)

# 发送 POST 请求
try:
    response = requests.post(url, data=params)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print("请求失败:", e)
    exit()

# 解析 JSON 响应
try:
    data = response.json()
except ValueError:
    print("无法解析 JSON 响应")
    exit()

# 检查返回状态码
if data.get("resultcode") != "0":
    print("请求失败:", data.get("resultinfo"))
    exit()

# 遍历 channellist 并下载 zip 文件
channellist = data.get("channellist", [])
for item in channellist:
    chname = item.get("chname")
    file_url = item.get("url")
    ver = item.get("ver")

    if not chname or not file_url or not ver:
        print("缺少 chname、url 或 ver，跳过此条目")
        continue

    # 构建频道文件夹路径
    channel_dir = os.path.join(root_dir, chname)
    os.makedirs(channel_dir, exist_ok=True)

    # 从 URL 提取原始文件名
    parsed_url = urlparse(file_url)
    file_name = os.path.basename(parsed_url.path)
    file_path = os.path.join(channel_dir, file_name)

    # 用 ver 作为解压文件夹名
    ver_parts = ver.split(".")
    if len(ver_parts) < 3:
        print(f"ver 格式不正确，使用原名: {ver}")
        extract_folder = ver
    else:
        extract_folder = ver_parts[2]
    extract_path = os.path.join(channel_dir, extract_folder)

    print(f"正在下载: {file_name} 到 {channel_dir}")
    try:
        with requests.get(file_url, stream=True, timeout=10) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        print(f"已保存: {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")
        continue
    except IOError as e:
        print(f"写入文件失败: {e}")
        continue

    # 解压 zip 文件
    print(f"正在解压: {file_name} 到 {extract_path}")
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        print(f"已解压: {file_name}")
    except zipfile.BadZipFile:
        print(f"文件损坏或不是 zip 文件: {file_name}")
    except Exception as e:
        print(f"解压失败: {e}")
        continue

    # 删除 zip 文件
    try:
        os.remove(file_path)
        print(f"已删除 zip 文件: {file_path}")
    except Exception as e:
        print(f"删除文件失败: {e}")

    # 处理解压后的文件，解析xml
    xml_path = os.path.join(extract_path, 'layout_balance.xml')
    if not os.path.exists(xml_path):
        print(f"XML 文件不存在: {xml_path}")
        continue
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"XML 解析失败: {e}")
        continue

    # 从 <type> 标签获取 icon 文件名
    type_element = root.find('.//type')
    if type_element is None:
        print("未找到 <type> 标签，无法获取 icon 文件名")
        continue
    icon_src = type_element.get('src')
    if not icon_src:
        print("未找到 <type> 的 src 属性，无法获取 icon 文件名")
        continue
    icon_file = os.path.join(extract_path, icon_src)

    # 删除 icon 文件
    if os.path.exists(icon_file):
        try:
            os.remove(icon_file)
            print(f"已删除 icon 文件: {icon_file}")
        except Exception as e:
            print(f"删除 icon 文件失败: {e}")

    # 收集所有 <image> 标签的信息
    images_info = []
    for image in root.findall('.//image'):
        src = image.get('src')
        title = image.get('title')
        content = image.get('content')
        contenturl = image.get('contenturl')
        if src and title and content and contenturl:
            images_info.append((src, title, content, contenturl))

    # 重命名图片文件
    for src, title, content, contenturl in images_info:
        old_path = os.path.join(extract_path, src)
        if os.path.exists(old_path):
            try:
                ext = os.path.splitext(src)[1]
                new_filename = f"{title}{ext}"
                new_path = os.path.join(extract_path, new_filename)
                if os.path.exists(new_path):
                    try:
                        os.remove(new_path)
                        print(f"已删除同名文件: {new_path}")
                    except Exception as e:
                        print(f"删除同名文件失败: {e}")
                os.rename(old_path, new_path)
                print(f"已重命名文件: {old_path} -> {new_path}")
            except Exception as e:
                print(f"重命名文件失败: {e}")

    # 写入 desc.txt 文件
    desc_path = os.path.join(extract_path, 'desc.txt')
    try:
        with open(desc_path, 'w', encoding='utf-8') as f:
            for src, title, content, contenturl in images_info:
                f.write(f"{title}\n")
                f.write(f"{content}\n")
                f.write(f"{contenturl}\n\n")
        print(f"已生成 desc.txt 文件: {desc_path}")
    except Exception as e:
        print(f"写入 desc.txt 文件失败: {e}")

    # 删除 XML 文件
    try:
        os.remove(xml_path)
        print(f"已删除 layout_balance.xml 文件: {xml_path}")
    except Exception as e:
        print(f"删除 XML 文件失败: {e}")

    #分隔不同频道的输出
    print("")

print("\n**********\n任务完成。\n**********\n")
