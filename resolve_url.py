from typing import Optional

def resolve(content: Optional[dict]) -> str:
    #print('Resolving!')
    if content is None:
        raise ValueError("内容为空，无法解析图片URL")
    try:
        url_all = content['response']['posts'][0]['post']['photoLinks']
        return url_all
    except KeyError:
        raise ValueError("无法解析图片URL，缺少必要的字段")
    

def fetch(url_all : list) -> tuple[list,int]:
    import json
    re = []
    error_count = 0
    for i in url_all:
        _full = json.loads(i)
        for full in _full:
            try:
                re.append(full['raw'])
            except KeyError:
                error_count += 1
                continue
    return re, error_count
