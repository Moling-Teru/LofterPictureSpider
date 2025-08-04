# LofterPictureSpider
利用手机端API简单实现了爬取Lofter图片（目前新增文本，视频）。
<div align="right"><img src="img.png" width = 128 height = 128 alt="Lofter Icon"></div>

## 如何使用？
> [!TIP]
> 为防止爬取过快被封IP，本repo使用代理池。\
> 代理池来源：[Python3WebSpider / ProxyPool](https://github.com/Python3WebSpider/ProxyPool)\
> 默认在localhost:5555运行，如有其他代理池，\
> 请在[simple_get_post_details.py](simple_get_post_details.py)，[lofter_api.py](lofter_api.py)，[just_get_it.py](just_get_it.py)中修改。\
> 不使用代理池，请将以上文件中requests部分的proxies删除。\
> 目前测试看来Lofter的防爬措施不严格，单IP不用代理也可以试着玩玩。

使用前请先安装依赖。
**程序入口为[launcher.py](launcher.py)，程序设置位于[config.yaml](config.yaml)。**

爬虫内容保存在contents目录下。如果有内容下载失败，链接会保存在errors.txt中。\
图片格式统一为png，文本格式为html，视频格式为mp4。
详细信息可以观察内容文件夹中的log。

> [!IMPORTANT]
> 重试下载可以使用[retry_it.py](retry_it.py)。但是目前只支持图片下载，且如果重试下载成功，请手动清空errors.txt。

默认最大进程数为3，如果需要修改，请在[launcher.py Line-44](https://github.com/Moling-Teru/LofterPictureSpider/blob/main/launcher.py#L44)中修改。

### 已知问题

- Lofter目前API受限，只能获取到前1000个帖子。对于大部分热门tag的榜单，尤其是总榜，基本是半报废状态。
- 彩蛋内容需要完整Cookie和云端校验，没法绕过，必须付费。短期内没有开发通过Cookie获取已经付费的内容的计划。
