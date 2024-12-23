# 目标
这个项目是根据提供的订阅地址,生成一个可以使用的v2ray的配置地址

# 测试
- 在ubuntu的v2ray中测试通过

# 使用帮助
## 打印订阅中的vmess节点
> python update_proxy.py --name

## 指定vmess节点列表,生成配置文件
> python aa.py 订阅地址 --ps "01-中转-2x-流媒体全解锁" "02-中转-2X-流媒体全解锁"
