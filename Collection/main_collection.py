import os.path
import argparse
import time
import requests
from requests.adapters import HTTPAdapter
from typing import Optional, Tuple, Dict, Any, List, Generator
import json
import yaml
import color
import dominate
from dominate.tags import div, p, h2, meta
from dominate.util import raw
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
from pathlib import Path


collection_url = 'https://api.lofter.com/v1.1/postCollection.api'

cl = color.Color()

s = requests.Session()
s.mount('http://', HTTPAdapter(max_retries=3))
s.mount('https://', HTTPAdapter(max_retries=3))

def get_proxies(num: int, require: bool) -> List[Dict | None]:
    if not require:
        return [None]
    headers={
        'Connection': 'Close'
    }
    proxies = []  # 存储获取到的代理
    try:
        with open('proxy_api.txt','r', encoding='utf-8') as f:
            proxy_api = f.read().strip()
            if not proxy_api:
                raise ValueError("代理API地址为空，请检查proxy_api.txt文件。")
        response = requests.get(
            f'https://api.douyadaili.com/proxy/?service=GetIp&authkey={proxy_api}&num={num}&lifetime=3&prot=1&format=json',
            headers=headers, timeout=5
        )
        if response.status_code != 200:
            raise RuntimeError('代理池请求失败，状态码: {}'.format(response.status_code))
        else:
            data = response.json()
            for one in data['data']:
                proxy_ip = one['ip']
                proxy_port = one['port']
                proxy = {
                    'http': f'http://{proxy_ip}:{proxy_port}',
                    'https': f'http://{proxy_ip}:{proxy_port}'
                }
                proxies.append(proxy)
            return proxies
    except TimeoutError:
        raise TimeoutError('代理池请求超时，请检查网络连接或代理池服务是否正常。')
    except json.JSONDecodeError:
        raise RuntimeError('代理池返回格式有误。')

def get_list(offset: int, blogname: str, cert: str, collection_id: int, proxies: dict = None) -> Optional[str]:
    headers = {
        'User-Agent': 'LOFTER-Android 8.2.23 (RMX3888; Android 9; null) WIFI',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip',
        'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
        'lofproduct': 'lofter-android-8.2.23',
        'lofter-phone-login-auth': cert
    }

    params = {
        'product': 'lofter-android-8.2.23'
    }

    body = {
        "supportposttypes": "1,2,3,4,5,6",
        "blogdomain": blogname,
        "offset": str(offset*15),
        "method": "getCollectionDetail",
        "collectionid": str(collection_id),
        "order": "1",
        "limit": "15"
    }

    response = s.post(collection_url, headers=headers, params=params,
                            data=body, timeout=10, proxies=proxies)

    if response.status_code == 200:
        return response.text
    else:
        raise requests.exceptions.ConnectionError(f'获取合集列表时服务器返回异常，状态码：{response.status_code}')


def get_collection_amount(response: str) -> Optional[int]:
    try:
        data = json.loads(response)
        if data['meta']['status'] != 200:
            raise RuntimeError(f'服务器返回合集列表内容异常，状态码：{data['meta']['status']}')
        return int(data['response'].get('collection',0).get('postCount',0))
    except json.JSONDecodeError:
        print("响应内容不是有效的JSON格式。")
        return None
    except Exception as e:
        print(f'未知异常：{str(e)}')
        return None

def get_collection_detail(response: str) -> Generator[tuple[list[int | str], int], Any, None]:
    try:
        content = json.loads(response)
        for part in content['response']['items']:
            if not part:
                return None
            try:
                if json.loads(part.get('misc', None)).get('postHide', None) in [str(1),1]:
                    continue
            except AttributeError:
                return None
            post_id : int = int(part['post']['id'])
            blogname : str = part['post']['blogInfo']['blogName']
            # Lofter API中，type 4 为视频，type 2 为图片，type 1 为文章
            # 本程序中，type 1 为图片，type 0 为文章，type 2 为视频
            content_type : int = int(part['post']['type'])
            if content_type == 1:
                content_type = 0
            elif content_type == 2:
                content_type = 1
            elif content_type == 4:
                content_type = 2
            else:
                try:
                    print(f'{cl.get_colour('RED')}未知的Content-Type：{content_type}，跳过该帖子。')
                    if not os.path.exists('collection/log'):
                        os.makedirs('collection/log')
                    with open('collection/log/error_details.json', 'a', encoding='utf-8') as file:
                        json.dump(content, file, ensure_ascii=False, indent=4)
                    print(f'本次请求的json文件已经保存。请附带该文件在github上提issue！{cl.reset()}')
                    continue
                except Exception as e:
                    print(f'{cl.get_colour('RED')}无法保存错误日志：{str(e)}{cl.reset()}')
                    continue
            yield [post_id, blogname], content_type

    except json.JSONDecodeError:
        raise ValueError("响应内容不是有效的JSON格式。")

def get_post_details(cert: str, blog_domain: str, post_id: int, proxy: dict = None) -> Optional[Dict[str, Any]]:
    url = "https://api.lofter.com/oldapi/post/detail.api"

    # 构建请求头
    headers = {
        "x-device": "",
        "lofproduct": "lofter-android-8.2.23",
        "user-agent": "LOFTER-Android 8.2.23 (RMX3888; Android 9; null) WIFI",
        "accept-encoding": "gzip",
        "content-type": "application/x-www-form-urlencoded",
        "lofter-phone-login-auth": cert
    }

    # URL参数
    params = {
        "product": "lofter-android-8.2.23"
    }

    # 请求体数据
    body_data = {
        "supportposttypes": "1,2,3,4,5,6",
        "blogdomain": f'{blog_domain}.lofter.com',
        "offset": "0",
        "requestType": "0",
        "postdigestnew": "1",
        "postid": str(post_id),
        "checkpwd": "1",
        "needgetpoststat": "1"
    }

    try:
        # 发送POST请求
        response = s.post(
            url=url,
            headers=headers,
            params=params,
            data=body_data,
            timeout=30,
            proxies=proxy  # 不需要代理可以删除
        )
        # 检查响应状态码
        response.raise_for_status()
        # 检查响应内容是否为空
        if not response.text.strip():
            print('响应为空。')
            return None

        # 返回原始JSON响应
        json_data = response.json()
        # 检查API返回的状态
        if 'meta' in json_data and json_data['meta'].get('status') != 200:
            print(f'---> X  状态码异常({json_data['meta'].get('status')})。')
            print(json_data['msg'])
            return None
        return json_data

    except Exception as e:
        # 静默处理所有异常，返回None
        print(f'---> X  未知异常：{str(e)}')
        return None

def resolve_article(json_info: dict | None) -> str | None:
    try:
        if isinstance(json_info, dict):
            content = json_info['response']['posts'][0]['post']['content'].strip()
            returnContent = json_info['response']['posts'][0]['post'].get('returnContent',[None])[0]
            if returnContent:
                returnContent = returnContent.get('content', None)
                returnContent = '<h3>以下为彩蛋内容</h3>\n<p id="GiftContent" style="white-space: pre-line;">' + returnContent + '</p>'
                return content + '\n' +returnContent
            else:
                return content
        else:
            return None

    except KeyError as e:
        print(f"解析JSON时发生错误: {e}")
        return None

def resolve_picture(content: Optional[dict]) -> str:
    if content is None:
        raise ValueError("内容为空，无法解析图片URL")
    try:
        url_all : list = list(json.loads(content['response']['posts'][0]['post']['photoLinks']))
        returnContent = content['response']['posts'][0]['post'].get('returnContent',None)
        if returnContent:
            return_img_all = returnContent[0]['images']
            for i in return_img_all:
                url_all.append(i)
        return str(url_all).replace("'", '"').replace('True','true').replace('False','false')  # 将单引号替换为双引号，确保JSON格式正确
    except KeyError:
        raise ValueError("无法解析图片URL，缺少必要的字段")

def resolve_video(content: Optional[dict]) -> Optional[str]:
    if content is None:
        raise ValueError('内容为空，无法解析视频URL')
    try:
        url_all = content['response']['posts'][0]['post'].get('embed', None)
        url = json.loads(url_all).get('originUrl', None)
        return url
    except KeyError:
        print('获取视频URL出现错误。')
        return None

def fetch(url: str, c_type: int, id: int, blogname: str, title: str, gift: int) -> tuple[list,int,int]:
    re = []
    error_count = 0
    if c_type == 1:  # 图片
        try:
            _full = json.loads(url)
        except json.decoder.JSONDecodeError as e:
            start = max(0, e.pos - 20)
            end = min(len(url), e.pos + 20)
            print(f"错误附近的内容: {repr(url[start:end])}")
            raise RuntimeError('解码JSON时发生错误。')
        for full in _full:
            try:
                re.append([full['raw'], id, blogname, title, gift])
            except KeyError:
                error_count += 1
                continue
    elif c_type == 0 or c_type == 2:  # 文字 视频
        re.append([url, id, blogname, title, gift])  # 原样返回
        # 应该不会有错误吧
    return re, error_count, c_type

class GetPostDetails:
    def __init__(self, info: tuple[list, int], proxy, cert) -> None:
        """
        Input:
        id: tuple 第一项list：[帖子ID, 作者域名]  第二项int: 0-文字，1-图片，2-视频
        """
        self.id = info[0][0]  # 帖子ID
        self.domain = info[0][1]  # 作者域名
        self.content_type = info[1]
        self.content = get_post_details(cert, self.domain, self.id, proxy)
        if self.content is None:
            print('获取帖子内容失败。')
            with open('collection/errors.txt', 'a', encoding='utf-8') as file:
                file.write(f'获取帖子内容失败: {self.id}, {self.domain}\n')
                raise IOError
        else:
            print(f"帖子ID & 作者域名: [{self.id}, {self.domain}]")

    def __call__(self) -> Optional[str]:
        try:
            js_result = self.content  # 先拉取整个帖子的json
            if self.content_type == 1:  # 图片
                url = resolve_picture(js_result)  # 初步解析图片链接部分
            elif self.content_type == 0:  # 文字
                url = resolve_article(js_result)  # 提取文字内容部分
            elif self.content_type == 2:  # 视频
                url = resolve_video(js_result)
            else:
                raise ValueError("未知的内容类型")

        except (KeyError, ValueError):
            url = None  # 如果解析失败，返回None
            print(f"{cl.get_colour('RED')}解析帖子URL时出错。{cl.reset()}")

        return url

    def get_gift(self) -> Optional[int]:
        """
        获取帖子是否需要付费
        :return: 0-不需要付费，1-需要付费
        """
        if self.content is None:
            raise ValueError("内容为空，无法解析付费信息")
        try:
            return self.content['response']['posts'][0]['post']['showGift']
        except KeyError:
            raise ValueError("无法解析付费信息，缺少必要的字段")

    def get_type(self) -> int:
        """
        获取内容类型
        :return: 0-文字，1-图片， 2-视频
        """
        return self.content_type

    def get_info(self) -> Tuple[int, str]:
        return self.id, self.domain

    def get_title(self) -> str:
        return self.content['response']['posts'][0]['post']['title'] if self.content else ""

def get_pic(url: str, save_path: str, id: int, blogname: str, title: str, gift: int, i: int, proxy: dict | None) -> None:
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
        response = s.get(url, timeout=30, headers=headers, params=params, proxies=proxy) # 无需代理可以删除proxies
        response.raise_for_status()  # 检查请求是否成功
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"成功下载图片: {url}")

        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"Title: {title}, ID: {id}, Blogname: {blogname}, Gift: {gift}, URL: {url}, Path: {save_path}\n")

    except Exception as e:
        with open('collection/errors.txt', 'a', encoding='utf-8') as f:
            f.write(f"{url}\n")
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"---> X  Error Downloading: Title: {title}, ID: {id}, Blogname: {blogname}, Gift: {gift}, URL: {url}")
            raise RuntimeError(f"下载图片失败: {url}，错误信息：{e}")

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
            div(h2('含有彩蛋，该爬虫获取内容可能不全。',id='PayWarning'),id='payWarningDiv')
            div(p(raw(content),id='postContent', style='font-size: 16px; line-height: 1.6;'),id='postContentDiv')
        with open(f'{save_path.split('.')[0]}.html', 'w', encoding='utf-8') as f:
            f.write(str(doc))
        print(f"成功保存文字内容: {save_path.split('.')[0]}.html")

        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"Title: {title}, ID: {id}, Blogname: {blogname}, Gift: {gift}, Path: {save_path.split('.')[:-1][0]}.html\n")

    except Exception as e:
        with open('collection/errors.txt', 'a', encoding='utf-8') as f:
            f.write(f"文字内容： {id}, {blogname}\n")
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"---> X  Error downloading: Title: {title}, ID: {id}, Blogname: {blogname}, Gift: {gift}")
            raise RuntimeError(f"保存文字内容失败: {url}，错误信息：{e}")

def get_video(url: str, save_path: str, id: int, blogname: str, title: str, gift: int, i: int, proxy: dict | None) -> None:  #todo 完善视频逻辑
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
                         proxies=proxy)  # 无需代理可以删除proxies
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
        with open('collection/errors.txt', 'a', encoding='utf-8') as f:
            f.write(f"{url}\n")
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"---> X  Error downloading: Title: {title}, ID: {id}, Blogname: {blogname}, Gift: {gift}, URL: {url}")
            raise RuntimeError(f"下载视频失败: {url}，错误信息：{e}")

class Get:
    def __init__(self,content_list: list, path: str, i: int) -> None :
        self.url = content_list[0]  # 帖子URL
        self.path = path
        self.id = content_list[1]  # 帖子ID
        self.blogname = content_list[2]  # 作者域名
        self.title = content_list[3]  # 帖子标题
        self.gift = content_list[4]  # 是否需要付费
        self.i = i

    def okget(self, content_type: int, proxy: Optional[dict] = None):
        if content_type == 1: #图片
            get_pic(self.url, self.path, self.id, self.blogname, self.title, self.gift, self.i, proxy)
        elif content_type == 0: #文字
            get_article(self.url, self.path, self.id, self.blogname, self.title, self.gift, self.i)
        elif content_type == 2:  # 视频
            get_video(self.url, self.path, self.id, self.blogname, self.title, self.gift, self.i, proxy)
        else:
            raise ValueError("未知的内容类型")


def load_config(target:str) -> Any:
    cfg_path = Path(__file__).with_name('config.yaml')
    with open(cfg_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        try:
            result = config[target]
        except KeyError:
            return None
    return result

def get_time() -> str:
    import datetime

    now = datetime.datetime.now()
    return now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]


def main():  # 请求单个offset，launcher里面塞多offset多线程
    parser = argparse.ArgumentParser(description='Lofter爬虫--抓取我的合集')
    parser.add_argument('--proxies', default=0)
    parser.add_argument('-n',default=0)
    parser.add_argument('--path', default='')

    args = parser.parse_args()
    if_proxies = bool(int(args.proxies))
    n = int(args.n)
    path = args.path

    print(f'第{n}次--正在初始化，请稍后...')

    cert = load_config('cert')
    blogname = load_config('blogname')
    collection_id = load_config('collection_id')

    # 开始抓list
    print(f'{cl.get_colour("BLUE")}{get_time()}：初始化完成，开始抓取合集列表...{cl.reset()}')
    contents = get_list(int(n), blogname=blogname, cert=cert, collection_id=collection_id, proxies = get_proxies(1, require=if_proxies)[0])
    content_generator = get_collection_detail(contents)

    # generator到手，开始请求每一个帖子 照搬原来的代码
    none_all = 0  # 统计无效链接的数量
    url_all = 0
    errors = 0
    content_lists = []
    content_types_list = []
    for post in content_generator:
        if post is None:
            none_all += 1
            print(f"{cl.get_colour('RED')}帖子内容为空，跳过该帖子。{cl.reset()}")
            continue
        try:
            p = GetPostDetails(post, proxy=get_proxies(1, require=if_proxies)[0], cert=cert)
        except IOError:
            continue
        url = p()
        c_type = p.get_type()  # 使用get_url函数获取每个帖子的URL
        gift = p.get_gift()  # 获取每个帖子的付费信息
        id = p.get_info()[0]  # 获取帖子ID
        domain = p.get_info()[1]  # 获取作者域名
        title = p.get_title()  # 获取帖子标题
        if url is None:  # 统计无效链接的数量
            none_all += 1
        else:
            url_all += 1
        results = fetch(url, c_type, id, domain, title, gift)
        for i in results[0]:
            content_lists.append(i)
        error_count = results[1]
        errors += error_count  # 统计无效链接的数量
        for i in range(len(results[0])):
            content_types_list.append(results[2])
        time.sleep(random.random()/1.25)  #随机间隔，防止ip被ban

    if none_all:
        print(f"获取帖子URL完成: {get_time()}, 共{url_all}项。{cl.get_colour('RED')}有{none_all}项无效链接。{cl.reset()}")
    else:
        print(f"获取帖子URL完成: {get_time()}, 共{url_all}项。{cl.get_colour('GREEN')}全部链接有效。{cl.reset()}")
    if errors:
        print(f"获取内容URL完成: {get_time()}, 共{len(content_lists)}项。{cl.get_colour('RED')}有{errors}项无效链接。{cl.reset()}")
    else:
        print(f"获取内容URL完成: {get_time()}, 共{len(content_lists)}项。{cl.get_colour('GREEN')}全部链接有效。{cl.reset()}")

    # 这里开始，注意力转移到Content_lists和content_types_list上，准备下载内容
    # 依然照搬原来的代码
    # 内容检查，看看content和types之间是否匹配
    if len(content_lists) != len(content_types_list):
        raise ValueError(
            f"内容列表({len(content_lists)})和类型列表长度({len(content_types_list)})不匹配，请检查数据源。")

    max_workers = 5  # 设置最大工作线程数，可根据需要调整
    download_error = 0  # 统计下载错误的数量
    proxy = get_proxies(5, if_proxies)  # 获取mini代理池
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 创建下载任务
        future_to_url = {
            executor.submit(Get(content_list=content_list, path=f'{path}/{n}-{j + 1}.png', i=n).okget,
                            content_types_list[j], random.choice(proxy)):  # todo: 整理一下文字和图片的判断逻辑 尤其是url展开之后
                (j, content_list) for j, content_list in enumerate(content_lists)
        }

        # 处理完成的任务
        completed_count = 0
        total_count = len(content_lists)

        for future in as_completed(future_to_url):
            j, pic = future_to_url[future]
            completed_count += 1
            try:
                future.result()  # 获取结果，如果有异常会抛出
                print(f"进度: {completed_count}/{total_count} - 内容 {j + 1} 下载完成")
            except Exception as exc:
                download_error += 1
                print(f"进度: {completed_count}/{total_count} - 内容 {j + 1} 下载失败: {exc}")

    with open(f'{path}/download_log_{n}.txt', 'a', encoding='utf-8') as log:
        log.write(f"总共下载了{len(content_lists)}项内容。\n")
        log.write(f"无内容链接数量: {none_all}, 错误链接数量: {errors}\n")
        log.write(f"下载失败数量: {download_error}\n")
    print(f'{cl.get_colour("GREEN")}下载日志已保存到 {path}/download_log_{n}.txt{cl.reset()}')

    print(f"下载完成: {get_time()}")
    print(cl.get_colour('CYAN'))
    print('\n' + f'=' * 80 + '\n')
    print(cl.reset())

if __name__ == '__main__':
    start_time = time.time()
    print(f'{get_time()}：程序开始。')
    main()
    end_time = time.time()
    print(f'{get_time()}：程序结束。\n总耗时：{end_time - start_time:.2f}秒。')

