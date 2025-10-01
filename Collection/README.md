## 新功能！

现已支持按照合集采集图片、视频和小说！（虽然几乎没改什么代码就是了，但总算是个新功能）

### config填写方式

需要着重注意的是collection_id和blogname的填写。

在Lofter中找到一个合集之后，使用`复制链接`功能，得到如下的链接（For Example）：

```text
https://www.lofter.com/front/blog/collection/share?collectionId=23500896&incantation=hjyMMiPQaItY
```

注意`CollectionId`的值就是我们需要填写的`collection_id`。一般为8位数字。

而`blogname`的值则需要进入用户主页，并`复制链接`（For Example）：

```text
https://vitaminb999.lofter.com
```

则将`vitaminb999.lofter.com`填写在`blogname`中。不要填写`https://`。

务必注意合集的所属用户和填写的用户博客链接必须一致。

### 开始和结束位

依然为`start`与`end`。合集的默认单次请求传输15个博客，故`start`填n即为从第n\*15+1个开始采集，`end`填n即为采集到第n\*15个。