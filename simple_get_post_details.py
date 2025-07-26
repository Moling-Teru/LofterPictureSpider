import requests
from typing import Dict, Any, Optional

def get_post_details(post_id, blog_domain: str) -> Optional[Dict[str, Any]]:
    """
    根据帖子ID获取帖子详情的原始JSON数据
    
    Args:
        post_id: 帖子ID (整数)
        blog_domain: 博客域名 (字符串)
        
    Returns:
        Optional[Dict[str, Any]]: 帖子详情的原始JSON数据，如果请求失败则返回None
    """
    url = "https://api.lofter.com/oldapi/post/detail.api"
    
    # 构建请求头
    headers = {
        "x-device": "",
        "lofproduct": "lofter-android-8.2.23", 
        "user-agent": "LOFTER-Android 8.2.23 (RMX3888; Android 9; null) WIFI",
        "accept-encoding": "gzip",
        "content-type": "application/x-www-form-urlencoded"
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
        response = requests.post(
            url=url,
            headers=headers,
            params=params,
            data=body_data,
            timeout=30
        )
        
        # 检查响应状态码
        response.raise_for_status()
        
        # 检查响应内容是否为空
        if not response.text.strip():
            return None
        
        # 返回原始JSON响应
        json_data = response.json()
        
        # 检查API返回的状态
        if 'meta' in json_data and json_data['meta'].get('status') != 200:
            return None
            
        return json_data
        
    except Exception as e:
        # 静默处理所有异常，返回None
        print(f'未知异常：{str(e)}')
        return None
