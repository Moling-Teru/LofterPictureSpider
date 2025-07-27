import requests
import os


headers = {
        "User-Agent": "Reqable/2.21.1",
        "accept-encoding": "gzip"
        }
params = {
        "type": "png"
    }

if os.path.exists('error_pics.txt'):
    pass
else:
    raise FileNotFoundError("没有找到错误图片列表。")

with open('error_pics.txt', 'a') as f:
    for i,line in enumerate(f):
        request = requests.get(line.strip(), headers=headers, params=params)
        with open(f'retry_{i+1}.png','wb') as img_file:
            img_file.write(request.content)