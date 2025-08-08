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
    
def gift(content: Optional[dict]) -> int:
    """
    获取帖子是否需要付费
    :param content: json内容
    :return: 0-不需要付费，1-需要付费
    """
    if content is None:
        raise ValueError("内容为空，无法解析付费信息")
    try:
        return content['response']['posts'][0]['post']['showGift']
    except KeyError:
        raise ValueError("无法解析付费信息，缺少必要的字段")
    

def fetch(url: str, c_type: int, id: int, blogname: str, title: str, gift: int) -> tuple[list,int,int]:
    import json
    re = []
    error_count = 0
    if c_type == 1:  # 图片
        _full = json.loads(url)
        for full in _full:
            try:
                re.append([full['raw'], id, blogname, title, gift])
            except KeyError:
                error_count += 1
                continue
    elif c_type == 0:  # 文字
        re.append([url, id, blogname, title, gift])  # 原样返回
        # 应该不会有错误吧
    return re, error_count, c_type
