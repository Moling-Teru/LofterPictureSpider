import requests
import os
import datetime

headers = {
        "User-Agent": "Reqable/2.21.1",
        "accept-encoding": "gzip"
        }
params = {
        "type": "png"
        }

if os.path.exists('tags/errors.txt'):
    pass
else:
    raise FileNotFoundError("没有找到错误图片列表。")

time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
if not os.path.exists(f'contents/retry-{time}'):
    os.makedirs(f'contents/retry-{time}')

with open('tags/errors.txt', 'r') as f:
    for i,line in enumerate(f):
        if 'nos.netease.com' in line:
            address = line.split('/')[3]
            line = line.replace(f'nos.netease.com/{address}',f'{address}.lf127.net')
        if 'lf127' not in line:
            print(f"跳过无效URL: {line.strip()}")
            continue
        
        request = requests.get(line.strip(), headers=headers, params=params)
        with open(f'contents/retry-{time}/retry_{i+1}.png','wb') as img_file:
            img_file.write(request.content)
        print(f"已重试下载图片: {line.strip()}")