import requests
from requests.adapters import HTTPAdapter

s = requests.Session()
s.mount('http://', HTTPAdapter(max_retries=3))
s.mount('https://', HTTPAdapter(max_retries=3))

proxypool_url = "http://localhost:5555/random"


def get_random_proxy(url: str) -> dict:
    proxy = requests.get(url).text.strip()
    proxies = {'http': 'http://' + proxy}
    return proxies


def get_pic(url: str, save_path: str) -> None:
    """
    下载图片并保存到指定路径

    Args:
        url (str): 图片的URL
        save_path (str): 保存图片的路径
    """
    headers = {
        "User-Agent": "Reqable/2.21.1",
        "accept-encoding": "gzip"
        }
    params = {
        "type": "png"
    }
    if 'http://nos.netease.com' in url:
        address = url.split('/')[3]
        url = url.replace(f'http://nos.netease.com/{address}',f'https://{address}.lf127.net')
    try:
        response = s.get(url, timeout=30, headers=headers, params=params, proxies=get_random_proxy(proxypool_url)) # 无需代理可以删除proxies
        response.raise_for_status()  # 检查请求是否成功
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"成功下载图片: {url}")
    except Exception as e:
        print(f"下载图片失败: {url}，错误信息：{e}")
        with open('error_pics.txt', 'a') as f:
            f.write(f"{url}\n")
