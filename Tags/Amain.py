# -*- coding: utf-8 -*-
from Tags import extract_post_ids, just_get_it, get_article, lofter_api
import datetime, time
import simple_get_post_details
import resolve_url
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json
import random
#from multiprocessing import Pool
import color
from typing import Dict, Any, Optional, List, Tuple
import argparse
import sys

cl = color.Color()

# 代理可选。调整请至launcher.py.

def get_time():
    time = datetime.datetime.now()
    return time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

def get_proxies(num: int, require: bool) -> List[Dict | None]:
    """
    获取代理池中的代理列表
    :return: 代理列表
    """
    if not require:
        return [None]
    headers={
        'Connection': 'Close'
    }
    proxies = []  # 存储获取到的代理
    try:
        with open('proxy_api.txt', 'r', encoding='utf-8') as f:
            proxy_api = f.read().strip()
            if not proxy_api:
                raise ValueError("代理API地址为空，请检查proxy_api.txt文件。")
        response = requests.get(
            f'https://api.douyadaili.com/proxy/?service=GetIp&authkey={proxy_api}&num={num}&lifetime=15&prot=1&format=json',
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


class GetPostDetails:
    def __init__(self, info: tuple[list,int], proxy) -> None:
        self.id = info[0][0]    # 帖子ID
        self.domain = info[0][1]  # 作者域名
        self.content_type = info[1]
        """
        Input:
        id: tuple 第一项list：[帖子ID, 作者域名]  第二项int: 0-文字，1-图片
        """
        self.content = simple_get_post_details.get_post_details(self.id, self.domain, proxy)
        print(f"帖子ID & 作者域名: [{self.id}, {self.domain}]")

    def __call__(self) -> Optional[str]:
        try:
            js_result = self.content  #先拉取整个帖子的json
            if self.content_type == 1:  #图片
                url = resolve_url.resolve(js_result)  #初步解析图片链接部分
            elif self.content_type == 0:  #文字
                url = get_article.resolve(js_result)  #提取文字内容部分
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
        :return: 0-文字，1-图片
        """
        return self.content_type
    
    def get_info(self) -> Tuple[int, str]:
        return self.id, self.domain
    
    def get_title(self) -> str:
        return self.content['response']['posts'][0]['post']['title'] if self.content else ""
    

def load_config(target:str) -> Any:
    import yaml

    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        result = config[target]

    return result

def main(optional_header: Dict[str, str]) -> None:
    parser = argparse.ArgumentParser(description='Lofter爬虫主程序')
    parser.add_argument('--offset', default=0, help='offset设置')
    parser.add_argument('--path', default='', help='保存路径设置')
    parser.add_argument('--proxies', default='1')

    args = parser.parse_args()
    n = int(args.offset)
    path = args.path
    proxies_or_not = bool(int(args.proxies))

    # 调用LOFTER API，抓取tag下内容
    print(f"{cl.get_colour('BLUE')}抓取帖子ID-第{n+1}次: {get_time()}{cl.reset()}")
    proxy = get_proxies(1, proxies_or_not)[0]   # 获取1个代理
    response = lofter_api.request_lofter_with_custom_params(optional_header, offset=10 * n, proxy=proxy)

    if not response:
        raise RuntimeError("没有获取到数据，可能是网络问题或API超出范围。")
    
    print(f"抓取tag完成: {get_time()}")

    print(f'{get_time()} 开始分析帖子ID...')

    # 交给extract_post_ids处理，分析帖子ID
    posts = extract_post_ids.extract_post_ids(response)
    likes, likes_low = extract_post_ids.get_likes(response)
    print(f"分析完成: {get_time()}")

    # 处理喜欢数不满足跳出
    aim_likes = load_config('likes')
    if aim_likes is not None:
        if likes is None:
            print(f"{cl.get_colour('RED')}无法获取喜欢数。{cl.reset()}目前继续抓取。")
            pass
        elif likes < aim_likes:
            print(f"{cl.get_colour('YELLOW')}喜欢数({likes})小于目标值({aim_likes})，跳过本次抓取。{cl.reset()}")
            time.sleep(1.5)  # 等待1.5秒
            sys.exit(0)
        else:
            print(f"{cl.get_colour('GREEN')}喜欢数({likes})满足目标值({aim_likes})，继续抓取。{cl.reset()}")
    else:
        print(f"{cl.get_colour('YELLOW')}没有设置喜欢数限制，当前喜欢数({likes})。{cl.reset()}")

    #Lofter此处逻辑为调用API找到信息流对应个人主页链接
    print(f"{get_time()} 开始获取帖子URL...")

    none_all = 0  # 统计无效链接的数量
    url_all = 0
    errors = 0
    content_lists = []
    content_types_list = []
    # todo: 分流图片和文字
    for info in posts:  #posts结构：([a,b],c)
        if info[1] in [0,1]:
            p = GetPostDetails(info, proxy)  # 进入拉取单个帖子请求阶段
            url = p()
            c_type = p.get_type()  # 使用get_url函数获取每个帖子的URL
            gift = p.get_gift()  # 获取每个帖子的付费信息
            id = p.get_info()[0]  # 获取帖子ID
            domain = p.get_info()[1]  # 获取作者域名
            title = p.get_title()  # 获取帖子标题
            #todo: 批量下载帖子内容转移至循环内部，内存优化
            if url is None:   # 统计无效链接的数量
                none_all += 1
            else:
                url_all += 1
            results = resolve_url.fetch(url, c_type, id, domain, title, gift)
            for i in results[0]:
                content_lists.append(i)
            error_count = results[1]
            errors += error_count  # 统计无效链接的数量
            for i in range(len(results[0])):
                content_types_list.append(results[2])
        elif info[1] == 2:  # 视频
            url_all += 1
            content_lists.append(info[0])
            content_types_list.append(2)


    if none_all:
        print(f"获取帖子URL完成: {get_time()}, 共{url_all}项。{cl.get_colour('RED')}有{none_all}项无效链接。{cl.reset()}")
    else:
        print(f"获取帖子URL完成: {get_time()}, 共{url_all}项。{cl.get_colour('GREEN')}全部链接有效。{cl.reset()}")


    if errors:
        print(f"获取内容URL完成: {get_time()}, 共{len(content_lists)}项。{cl.get_colour('RED')}有{errors}项无效链接。{cl.reset()}")
    else:
        print(f"获取内容URL完成: {get_time()}, 共{len(content_lists)}项。{cl.get_colour('GREEN')}全部链接有效。{cl.reset()}")  #todo: 直到这边都排障完成

    # 使用多线程下载图片 todo: 增加图片信息文本说明

    # 内容检查，看看content和types之间是否匹配
    if len(content_lists) != len(content_types_list):
        raise ValueError(f"内容列表({len(content_lists)})和类型列表长度({len(content_types_list)})不匹配，请检查数据源。")

    max_workers = 5  # 设置最大工作线程数，可根据需要调整
    download_error = 0  # 统计下载错误的数量
    proxy = get_proxies(5, proxies_or_not)  # 获取mini代理池
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 创建下载任务
        future_to_url = {
            executor.submit(just_get_it.Get(content_list=content_list, path=f'{path}/{n}-{j + 1}.png', i=n).okget, content_types_list[j], random.choice(proxy)):  #todo: 整理一下文字和图片的判断逻辑 尤其是url展开之后
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
                print(f"进度: {completed_count}/{total_count} - 内容 {j+1} 下载完成")
            except Exception as exc:
                #download_error += 1
                print(f"进度: {completed_count}/{total_count} - 内容 {j+1} 下载失败: {exc}")

    with open(f'{path}/download_log_{n}.txt','a',encoding='utf-8') as log:
        log.write(f"总共下载了{len(content_lists)}项内容。\n")
        log.write(f"最高喜欢数: {likes}, 最低喜欢数: {likes_low}\n")
        log.write(f"无效链接数量: {none_all}, 错误链接数量: {errors}\n")
        #log.write(f"下载错误数量: {download_error}\n")
    print(f'{cl.get_colour("GREEN")}下载日志已保存到 {path}/download_log_{n}.txt{cl.reset()}')

    print(f"下载完成: {get_time()}")
    print(cl.get_colour('CYAN'))
    print('\n' + f'=' * 80 + '\n')
    print(cl.reset())

if __name__ == "__main__":

    start_time=time.time()
    print(f"{get_time()}：程序开始。")
    print(cl.get_colour('CYAN'))
    print('\n' + f'=' * 80 + '\n')
    print(cl.reset())

    optional_header={
        'tag': load_config('tag'), # 标签，自行填写
        'type': load_config('type') #date, week, month, total
    }

    main(optional_header)

    end_time = time.time()
    print(f"{cl.get_colour('YELLOW')}总耗时: {end_time - start_time:.3f}秒{cl.reset()}")
    time.sleep(1)
    sys.exit(0)
    #完美结束！