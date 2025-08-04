import requests
import json
from typing import Dict, Any, Optional
import just_get_it

def request_lofter_tag_posts(tag: str, offset: str = "0") -> Optional[Dict[str, Any]]:
    """
    请求LOFTER API获取标签下的帖子信息
    
    Args:
        tag (str): 标签名称，默认为"大黑塔"
        offset (str): 偏移量，默认为"0"
        
    Returns:
        Optional[Dict[str, Any]]: API响应的JSON数据，如果请求失败则返回None
    """
    url = "https://api.lofter.com/newapi/tagPosts.json"
    
    # 构建请求体数据
    body_data = {
        "product": "lofter-android-8.2.23",
        "postTypes": "",
        "offset": offset,
        "postYm": "",
        "returnGiftCombination": "",
        "recentDay": "0",
        "protectedFlag": "0",
        "range": "0",
        "firstpermalink": "null",
        "style": "0",
        "tag": tag,
        "type": "date"
    }
    
    # 构建请求头（保留指定的几项）
    headers = {
        "x-device": "",
        "lofproduct": "lofter-android-8.2.23",
        "user-agent": "LOFTER-Android 8.2.23 (RMX3888; Android 9; null) WIFI",
        "accept-encoding": "gzip",  # 只使用gzip，避免brotli
        "content-type": "application/x-www-form-urlencoded; charset=utf-8",
        # content-length 会由 requests 自动计算
    }
    
    try:
        # 发送POST请求
        response = requests.post(
            url=url,
            headers=headers,
            data=body_data,
            timeout=30,
            proxies=just_get_it.get_random_proxy('http://localhost:5555/random')  # 不需要代理可以删除
        )
        
        # 检查响应状态码
        response.raise_for_status()
        
        # 检查响应内容是否为空
        if not response.text.strip():
            print("响应内容为空")
            return None
        
        # 返回JSON响应
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"网络请求失败: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        return None
    except Exception as e:
        print(f"发生未知错误: {e}")
        return None


def request_lofter_with_custom_params(body_params: Dict[str, str] ,offset: int) -> Optional[Dict[str, Any]]:
    """
    使用自定义参数请求LOFTER API
    
    Args:
        body_params (Dict[str, str]): 自定义的请求体参数
        
    Returns:
        Optional[Dict[str, Any]]: API响应的JSON数据，如果请求失败则返回None
    """
    url = "https://api.lofter.com/newapi/tagPosts.json"
    
    # 默认的请求体参数
    default_body = {
        "product": "lofter-android-8.2.23",
        "postTypes": "",
        "offset": str(offset),
        "postYm": "",
        "returnGiftCombination": "",
        "recentDay": "0",
        "protectedFlag": "0",
        "range": "0",
        "firstpermalink": "null",
        "style": "0",
    }
    
    # 合并自定义参数
    body_data = {**default_body, **body_params}
    
    # 构建请求头
    headers = {
        "x-device": "",
        "lofproduct": "lofter-android-8.2.23",
        "user-agent": "LOFTER-Android 8.2.23 (RMX3888; Android 9; null) WIFI",
        "accept-encoding": "gzip",  # 只使用gzip，避免brotli
        "content-type": "application/x-www-form-urlencoded; charset=utf-8"
    }
    
    try:
        response = requests.post(
            url=url,
            headers=headers,
            data=body_data,
            timeout=30
        )
        
        response.raise_for_status()
        
        if not response.text.strip():
            print("响应内容为空")
            return None

        if response.json()['data']['offset'] == -1:
            return None
            
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"网络请求失败: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        return None
    except Exception as e:
        print(f"发生未知错误: {e}")
        return None
