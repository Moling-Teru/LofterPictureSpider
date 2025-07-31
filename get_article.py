from typing import Optional, Any

def resolve(json_info: dict | None) -> str | None:
    try:
        if isinstance(json_info, dict):
            content = json_info['response']['posts'][0]['post']['content'].strip().replace('\n', '')
            return content
        else:
            return None
    
    except KeyError as e:
        print(f"解析JSON时发生错误: {e}")
        return None