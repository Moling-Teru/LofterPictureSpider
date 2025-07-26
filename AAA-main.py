import lofter_api
import extract_post_ids
import datetime, time
import simple_get_post_details
import resolve_url
import get_pic
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Pool
import color
from typing import Dict, Any, Optional, List
cl = color.Color()

def get_time():
    time = datetime.datetime.now()
    return time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

def check_folder() -> str:
    import os
    if not os.path.exists('images'):
        os.makedirs('images')
    path=f'images/{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}'
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def get_url(id: tuple[int, Any]) -> str | None:
    try:
        print(f"帖子ID & 作者域名: {id}")
        js_result = simple_get_post_details.get_post_details(id[0], id[1])  #先拉取整个帖子的json
        url = resolve_url.resolve(js_result)  #再初步解析整个帖子中的图片链接部分
    except (KeyError, ValueError):
        url = None
    return url

if __name__ == "__main__":
    start_time=time.time()
    print(f"{get_time()}：开始抓取LOFTER帖子ID。")

    optional_header={
        'tag': '浅羽悠真', # 标签，自行填写
        'type': 'total' #date, week, month, total
    }
    path = check_folder()

    for i in range(3): # 这里循环n次，抓取10*n个帖子（包含可能的文字/视频帖）
        # 调用LOFTER API，抓取tag下内容
        response = lofter_api.request_lofter_with_custom_params(optional_header, offset=10*i)
        if not response:
            raise RuntimeError("没有获取到数据，可能是网络问题或API错误")
        print(f"抓取完成: {get_time()}")

        print(f'{get_time()} 开始分析帖子ID...')
        # 交给extract_post_ids处理，分析帖子ID
        posts = extract_post_ids.extract_post_ids_with_photos(response)
        print(f"分析完成: {get_time()}")


        #Lofter此处逻辑为调用API找到信息流对应个人主页链接
        url_all = []
        id_all = []
        print(f"{get_time()} 开始获取帖子URL...")
        for id in posts:
            id_all.append(id)
        with Pool(5) as p:   #可设置最大进程数
            url_all = p.map(get_url,id_all)
        none_all = url_all.count(None)
        url_all = list(filter(None, url_all))
        if none_all:
            print(f"获取帖子URL完成: {get_time()}, 共{len(url_all)}项。{cl.get_colour('RED')}有{none_all}项无效链接。{cl.reset()}")
        else:
            print(f"获取帖子URL完成: {get_time()}, 共{len(url_all)}项。{cl.get_colour('GREEN')}全部链接有效。{cl.reset()}")

        # 个人主页中包含所有图片链接，批量下载图片
        # 先获取图片链接
        print(f"{get_time()} 开始下载图片...")
        urls, errors = resolve_url.fetch(url_all)
        if errors:
            print(f"获取图片URL完成: {get_time()}, 共{len(urls)}项。{cl.get_colour('RED')}有{errors}项无效链接。{cl.reset()}")
        else:
            print(f"获取图片URL完成: {get_time()}, 共{len(urls)}项。{cl.get_colour('GREEN')}全部链接有效。{cl.reset()}")

        # 使用多线程下载图片
        max_workers = 5  # 设置最大工作线程数，可根据需要调整
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 创建下载任务
            future_to_url = {
                executor.submit(get_pic.get_pic, pic, f'{path}/{i}-{j+1}.png'): (j, pic) 
                for j, pic in enumerate(urls)
            }
            
            # 处理完成的任务
            completed_count = 0
            total_count = len(urls)
            for future in as_completed(future_to_url):
                j, pic = future_to_url[future]
                completed_count += 1
                try:
                    future.result()  # 获取结果，如果有异常会抛出
                    print(f"进度: {completed_count}/{total_count} - 图片 {j+1} 下载完成")
                except Exception as exc:
                    print(f"进度: {completed_count}/{total_count} - 图片 {j+1} 下载失败: {exc}")

        print(f"下载图片完成: {get_time()}")
        print(cl.get_colour('CYAN'))
        print('\n' + f'=' * 80 + '\n')
        print(cl.reset())

    end_time = time.time()
    print(f"{cl.get_colour('YELLOW')}总耗时: {end_time - start_time:.3f}秒{cl.reset()}")
