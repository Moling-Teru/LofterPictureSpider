import lofter_api
import extract_post_ids
import datetime
import simple_get_post_details
import resolve_url
import get_pic
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    
if __name__ == "__main__":
    print(f":{get_time()}：开始抓取LOFTER帖子ID。")

    optional_header={
        'tag': '男漂泊者', # 标签，自行填写
        'type': 'total' #date, week, month, total
    }

    # 调用LOFTER API，抓取tag下内容
    response = lofter_api.request_lofter_with_custom_params(optional_header, offset=0)
    if not response:
        raise RuntimeError("没有获取到数据，可能是网络问题或API错误")
    print(f"抓取完成: {get_time()}")

    print(f'{get_time()} 开始分析帖子ID...')
    # 交给extract_post_ids处理，分析帖子ID
    posts = extract_post_ids.extract_post_ids_with_photos(response)
    print(f"分析完成: {get_time()}")

    url_all = []
    print(f"{get_time()} 开始获取图片URL...")
    for id in posts:
        print(f"帖子ID & 作者域名: {id}")
        js_result = simple_get_post_details.get_post_details(id[0], id[1])
        url = resolve_url.resolve(js_result)
        url_all.append(url)
    print(f"获取图片URL完成: {get_time()}, 共{len(url_all)}项。")

    # 批量下载图片
    # 先获取图片链接
    path = check_folder()
    print(f"{get_time()} 开始下载图片...")
    urls = resolve_url.fetch(url_all)
    
    # 使用多线程下载图片
    max_workers = 5  # 设置最大工作线程数，可根据需要调整
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 创建下载任务
        future_to_url = {
            executor.submit(get_pic.get_pic, pic, f'{path}/{i+1}.png'): (i, pic) 
            for i, pic in enumerate(urls)
        }
        
        # 处理完成的任务
        completed_count = 0
        total_count = len(urls)
        for future in as_completed(future_to_url):
            i, pic = future_to_url[future]
            completed_count += 1
            try:
                future.result()  # 获取结果，如果有异常会抛出
                print(f"进度: {completed_count}/{total_count} - 图片 {i+1} 下载完成")
            except Exception as exc:
                print(f"进度: {completed_count}/{total_count} - 图片 {i+1} 下载失败: {exc}")
    
    print(f"下载图片完成: {get_time()}")
        