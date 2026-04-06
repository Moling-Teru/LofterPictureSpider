import json
from typing import Optional

def resolve(content: Optional[dict]) -> Optional[str]:
    if content is None:
        raise ValueError('内容为空，无法解析视频URL')
    try:
        url_all = content['response']['posts'][0]['post'].get('embed', None)
        url = json.loads(url_all).get('originUrl', None)
        return url
    except KeyError:
        print('获取视频URL出现错误。')
        return None