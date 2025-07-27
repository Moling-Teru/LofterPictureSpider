import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional, List, Union
import argparse

class LofterStressTest:
    """LOFTER API 压力测试类"""
    
    def __init__(self, concurrent_limit: int = 10, total_requests: int = 100, timeout: int = 30):
        self.concurrent_limit = concurrent_limit
        self.total_requests = total_requests
        self.timeout = timeout
        self.results: List[Union[Dict[str, Any], BaseException, None]] = []
        
    async def request_lofter_async(self, session: aiohttp.ClientSession, 
                                 body_params: Dict[str, str], 
                                 offset: int, 
                                 request_id: int) -> Optional[Dict[str, Any]]:
        """异步请求LOFTER API"""
        url = "https://api.lofter.com/newapi/tagPosts.json"
        
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
        
        body_data = {**default_body, **body_params}
        
        headers = {
            "x-device": "",
            "lofproduct": "lofter-android-8.2.23",
            "user-agent": "LOFTER-Android 8.2.23 (RMX3888; Android 9; null) WIFI",
            "accept-encoding": "gzip",
            "content-type": "application/x-www-form-urlencoded; charset=utf-8"
        }
        
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with session.post(url, headers=headers, data=body_data, timeout=timeout_obj) as response:
                response.raise_for_status()
                
                response_text = await response.text()
                if not response_text.strip():
                    print(f"请求{request_id}: 响应内容为空")
                    return None
                    
                result = await response.json()
                print(f"✓ 请求{request_id}: 完成 (offset={offset})")
                return result
                
        except asyncio.TimeoutError:
            print(f"✗ 请求{request_id}: 超时")
            return None
        except aiohttp.ClientError as e:
            print(f"✗ 请求{request_id}: 网络错误: {e}")
            return None
        except Exception as e:
            print(f"✗ 请求{request_id}: 未知错误: {e}")
            return None

    async def run_stress_test(self, tag: str = "青雀", post_type: str = "total") -> Dict[str, Any]:
        """运行压力测试"""
        optional_header = {
            'tag': tag,
            'type': post_type
        }
        
        print(f"🚀 开始 LOFTER API 压力测试")
        print(f"📊 测试配置:")
        print(f"   - 标签: {tag}")
        print(f"   - 类型: {post_type}")
        print(f"   - 总请求数: {self.total_requests}")
        print(f"   - 并发限制: {self.concurrent_limit}")
        print(f"   - 超时时间: {self.timeout}秒")
        print("=" * 60)
        
        start_time = time.time()
        
        connector = aiohttp.TCPConnector(
            limit=self.concurrent_limit, 
            limit_per_host=self.concurrent_limit
        )
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            semaphore = asyncio.Semaphore(self.concurrent_limit)
            
            async def controlled_request(request_id: int):
                async with semaphore:
                    return await self.request_lofter_async(
                        session, 
                        optional_header, 
                        offset=10 * request_id, 
                        request_id=request_id + 1
                    )
            
            tasks = [controlled_request(i) for i in range(self.total_requests)]
            
            print("⏳ 执行并发请求中...")
            self.results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 统计结果
            successful_requests = sum(
                1 for result in self.results 
                if result is not None and not isinstance(result, BaseException)
            )
            failed_requests = self.total_requests - successful_requests
            
            # 输出结果
            print("=" * 60)
            print("📈 压力测试结果:")
            print(f"   ⏱️  总耗时: {total_time:.2f}秒")
            print(f"   ✅ 成功请求: {successful_requests}")
            print(f"   ❌ 失败请求: {failed_requests}")
            print(f"   🚀 平均QPS: {self.total_requests / total_time:.2f}")
            print(f"   📊 成功率: {(successful_requests / self.total_requests) * 100:.1f}%")
            
            if total_time > 0:
                avg_response_time = total_time / self.total_requests
                print(f"   ⚡ 平均响应时间: {avg_response_time:.3f}秒")
            
            return {
                'total_time': total_time,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'qps': self.total_requests / total_time if total_time > 0 else 0,
                'success_rate': (successful_requests / self.total_requests) * 100,
                'avg_response_time': total_time / self.total_requests if total_time > 0 else 0
            }

def main():
    """主函数，支持命令行参数"""
    parser = argparse.ArgumentParser(description='LOFTER API 压力测试工具')
    parser.add_argument('--tag', default='青雀', help='搜索标签 (默认: 青雀)')
    parser.add_argument('--type', default='total', choices=['date', 'week', 'month', 'total'], 
                       help='帖子类型 (默认: total)')
    parser.add_argument('--requests', type=int, default=100, help='总请求数 (默认: 100)')
    parser.add_argument('--concurrent', type=int, default=10, help='并发数 (默认: 10)')
    parser.add_argument('--timeout', type=int, default=30, help='超时时间/秒 (默认: 30)')
    
    args = parser.parse_args()
    
    # 创建压力测试实例
    stress_test = LofterStressTest(
        concurrent_limit=args.concurrent,
        total_requests=args.requests,
        timeout=args.timeout
    )
    
    # 运行测试
    asyncio.run(stress_test.run_stress_test(tag=args.tag, post_type=args.type))

if __name__ == "__main__":
    main()
