import json
from typing import Generator, Dict, Any, List, Optional, Tuple
import time


def extract_post_ids(data: Dict[str, Any]) -> Generator[tuple[List[Any], int], None]:
    """
    从已解析的JSON数据中提取包含照片的帖子ID
    
    Args:
        data (Dict[str, Any]): 已解析的JSON数据
        
    Yields:
        int: 包含照片的帖子ID (photoCount > 0)
    """
    try:
        # 检查JSON结构是否正确
        if 'data' not in data or 'list' not in data['data']:
            print("JSON文件格式不正确：缺少 data.list 结构")
            return
        
        # 遍历list中的每一项
        for item in data['data']['list']:
            try:
                # 获取photoCount
                photo_count = item['postData']['postView']['photoCount']
                
                # 如果photoCount为0
                if photo_count == 0:  #todo 直接尝试返回最后一步所需的所有内容
                    if item['postData']['postView'].get('videoPostView', None):
                        post = [item['postData']['postView']['videoPostView']['videoInfo']['originUrl'],
                                item['postData']['postView']['id'],
                                item['blogInfo']['blogName'],
                                item['postData']['postView']['title'],
                                0], 2  # 视频 URL,ID,域名,标题,是否付费
                        yield post
                    else:
                        post = [item['postData']['postView']['id'], item['blogInfo']['blogName']], 0  #文字
                        yield post
                    
                
                # 如果photoCount不为0，返回post ID
                else:
                    post = [item['postData']['postView']['id'],item['blogInfo']['blogName']], 1  #图片
                    yield post
                
            except KeyError as e:
                print(f"跳过格式异常的项目，缺少字段: {e}")
                continue
                
    except json.JSONDecodeError:
        print(f"JSON文件格式错误")
    except Exception as e:
        print(f"读取文件时发生错误: {e}")

def get_likes(data: Dict[str, Any]) -> Optional[Tuple[int,int]]:
    try:
        likes = data['data']['list'][0]['postData']['postCount']['favoriteCount']
        likes_low = data['data']['list'][-1]['postData']['postCount']['favoriteCount']
        return likes, likes_low
    except json.JSONDecodeError:
        print(f"JSON文件格式错误")
        return None
    except KeyError as e:
        print(f"跳过格式异常的项目，缺少字段: {e}")
        return None
    except Exception as e:
        print(f'发生未知错误: {e}')
        print(data)
        time.sleep(3)
        return None