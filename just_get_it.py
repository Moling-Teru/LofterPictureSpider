import requests
from requests.adapters import HTTPAdapter
import dominate
from dominate.tags import div, p, a, h2, meta  # 只导入你实际用到的标签
from dominate.util import raw

s = requests.Session()
s.mount('http://', HTTPAdapter(max_retries=3))
s.mount('https://', HTTPAdapter(max_retries=3))

proxypool_url = "http://localhost:5555/random"


def get_random_proxy(url: str) -> dict:
    proxy = requests.get(url).text.strip()
    proxies = {'http': 'http://' + proxy}
    return proxies


def get_pic(url: str, save_path: str, id: int, blogname: str, title: str, gift: int, i: int) -> None:
    log_path = '/'.join(save_path.split('/')[:-1])  # 获取保存路径的目录
    log_file = f"{log_path}/download_log_{i}.txt"
    headers = {
        "User-Agent": "Reqable/2.21.1",
        "accept-encoding": "gzip"
        }
    params = {
        "type": "png"
        }
    if 'http://' not in url and 'https://' not in url:
        raise ValueError("URL格式错误，请确保URL以http://或https://开头。")
    if 'http://nos.netease.com' in url:
        address = url.split('/')[3]
        url = url.replace(f'http://nos.netease.com/{address}',f'https://{address}.lf127.net')
    try:
        response = s.get(url, timeout=30, headers=headers, params=params, proxies=get_random_proxy(proxypool_url)) # 无需代理可以删除proxies
        response.raise_for_status()  # 检查请求是否成功
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"成功下载图片: {url}")

        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"Title: {title}, ID: {id}, Blogname: {blogname}, Gift: {gift}, URL: {url}, Path: {save_path}\n")

    except Exception as e:
        print(f"下载图片失败: {url}，错误信息：{e}")
        with open('errors.txt', 'a', encoding='utf-8') as f:
            f.write(f"{url}\n")
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"Error Downloading: Title: {title}, ID: {id}, Blogname: {blogname}, Gift: {gift}, URL: {url}")


def get_article(url: str, save_path: str, id: int, blogname: str, title: str, gift: str, i: int) -> None:# 文字
    try:
        content = url
        log_path = '/'.join(save_path.split('/')[:-1])  # 获取保存路径的目录
        log_file = f"{log_path}/download_log_{i}.txt"
        if '<p' not in content:
            raise ValueError("内容格式错误，请确保内容包含HTML标签。")
        doc = dominate.document(title=title)
        with doc.head:
            meta(content="text/html; charset=UTF-8",http_equiv="Content-Type")
        with doc.body:
            div(h2('含有彩蛋，该爬虫获取内容不全。',id='PayWarning'),id='payWarningDiv')
            div(p(raw(content),id='postContent', style='font-size: 16px; line-height: 1.6;'),id='postContentDiv')
        with open(f'{save_path.split('.')[0]}.html', 'w', encoding='utf-8') as f:
            f.write(str(doc))
        print(f"成功保存文字内容: {save_path.split('.')[0]}.html")

        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"Title: {title}, ID: {id}, Blogname: {blogname}, Gift: {gift}, Path: {save_path.split('.')[:-1][0]}.html\n")

    except Exception as e:
        print(f"保存文字内容失败: {url}，错误信息：{e}")
        with open('errors.txt', 'a', encoding='utf-8') as f:
            f.write(f"文字内容： {id}, {blogname}\n")
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"Error downloading: Title: {title}, ID: {id}, Blogname: {blogname}, Gift: {gift}")


def get_video(url: str, save_path: str, id: int, blogname: str, title: str, gift: int, i: int) -> None:  #todo 完善视频逻辑
    headers = {
        "User-Agent": "Reqable/2.33.12",
        "accept-encoding": "gzip"
    }
    log_path = '/'.join(save_path.split('/')[:-1])  # 获取保存路径的目录
    log_file = f"{log_path}/download_log_{i}.txt"
    if 'http://' not in url and 'https://' not in url:
        raise ValueError("URL格式错误，请确保URL以http://或https://开头。")
    try:
        response = s.get(url, timeout=30, headers=headers,
                         proxies=get_random_proxy(proxypool_url))  # 无需代理可以删除proxies
        response.raise_for_status()  # 检查请求是否成功
        if response.status_code != 200:
            raise RuntimeError(f"下载失败，状态码: {response.status_code}")
        content_path = save_path.split('.')[0] + '.mp4'  # 假设视频保存为mp4格式
        with open(content_path, 'wb') as f:
            f.write(response.content)
        print(f"成功下载视频: {url.split('?')[0]}")

        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"Title: {title}, ID: {id}, Blogname: {blogname}, Gift: {gift}, URL: {url}, Path: {save_path}\n")

    except Exception as e:
        print(f"下载视频失败: {url}，错误信息：{e}")
        with open('errors.txt', 'a', encoding='utf-8') as f:
            f.write(f"{url}\n")
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"Error downloading: Title: {title}, ID: {id}, Blogname: {blogname}, Gift: {gift}, URL: {url}")



class Get:
    def __init__(self,content_list: list, path: str, i: int) -> None :
        self.url = content_list[0]  # 帖子URL
        self.path = path
        self.id = content_list[1]  # 帖子ID
        self.blogname = content_list[2]  # 作者域名
        self.title = content_list[3]  # 帖子标题
        self.gift = content_list[4]  # 是否需要付费
        self.i = i


    def okget(self, content_type: int):
        if content_type == 1: #图片
            get_pic(self.url, self.path, self.id, self.blogname, self.title, self.gift, self.i)
        elif content_type == 0: #文字
            get_article(self.url, self.path, self.id, self.blogname, self.title, self.gift, self.i)
        elif content_type == 2:  # 视频
            get_video(self.url, self.path, self.id, self.blogname, self.title, self.gift, self.i)
        else:
            raise ValueError("未知的内容类型")
