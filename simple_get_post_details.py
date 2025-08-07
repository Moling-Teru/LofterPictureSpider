import requests
from requests.adapters import HTTPAdapter
from typing import Dict, Any, Optional

s = requests.Session()
s.mount('http://', HTTPAdapter(max_retries=3))
s.mount('https://', HTTPAdapter(max_retries=3))

def get_post_details(post_id, blog_domain: str, proxy: dict = None) -> Optional[Dict[str, Any]]:
    """
    根据帖子ID获取帖子详情的原始JSON数据
    
    Args:
        post_id: 帖子ID (整数)
        blog_domain: 博客域名 (字符串)
        proxy: 代理设置 (字典)，如果不需要代理可以传入None
        
    Returns:
        Optional[Dict[str, Any]]: 帖子详情的原始JSON数据，如果请求失败则返回None
    """
    url = "https://api.lofter.com/oldapi/post/detail.api"
    proxy_url = 'http://localhost:5555/random'
    
    # 构建请求头
    headers = {
        "x-device": "",
        "lofproduct": "lofter-android-8.2.23", 
        "user-agent": "LOFTER-Android 8.2.23 (RMX3888; Android 9; null) WIFI",
        "accept-encoding": "gzip",
        "content-type": "application/x-www-form-urlencoded",
        "lofter-phone-login-auth": "wa6AZpw1DLn0Ua5ufjY7IkJChCgHDILU1BF1EIFsC568Ihf3SlEIkI3j870zccKt9dET0xLCTUUnmuJToM7WCoI9gUKkSl2u"
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
        #print('Ready to post!')
        # 发送POST请求
        response = s.post(
            url=url,
            headers=headers,
            params=params,
            data=body_data,
            timeout=30,
            proxies=proxy  # 不需要代理可以删除
        )
        #print('Get!')
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
            print(f'状态码异常({json_data['meta'].get('status')})。')
            return None
            
        return json_data
        
    except Exception as e:
        # 静默处理所有异常，返回None
        print(f'未知异常：{str(e)}')
        return None
    

# 测试区域
if __name__ == "__main__":
    # 测试获取帖子详情
    post_id = 11757071736  # 替换为实际的帖子ID
    blog_domain = "wo-cp99"  # 替换为实际的博客域名
    
    post_details = get_post_details(post_id, blog_domain)
    
    if post_details:
        with open('Likes/post_details_picture_paid_test.json', 'w', encoding='utf-8') as f:
            import json
            json.dump(post_details, f, ensure_ascii=False, indent=4)
    else:
        print("获取帖子详情失败或返回数据为空")
