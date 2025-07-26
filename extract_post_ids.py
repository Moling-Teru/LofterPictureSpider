import json
from typing import Generator, Dict, Any, Union

def extract_post_ids_with_photos(data: Dict[str, Any]) -> Generator[Union[int, str], None, None]:
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
                
                # 如果photoCount为0，跳过该项
                if photo_count == 0:
                    continue
                
                # 如果photoCount不为0，返回post ID
                post = [item['postData']['postView']['id'],item['blogInfo']['blogName']]
                yield post
                
            except KeyError as e:
                print(f"跳过格式异常的项目，缺少字段: {e}")
                continue
                
    except json.JSONDecodeError:
        print(f"JSON文件格式错误")
    except Exception as e:
        print(f"读取文件时发生错误: {e}")