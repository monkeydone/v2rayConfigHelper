# 目标
这个项目是根据提供的订阅地址,生成一个可以使用的v2ray的配置地址

# 测试
- 在ubuntu的v2ray中测试通过

# 使用帮助
## 打印订阅中的vmess节点
> python update_proxy.py --name

## 指定vmess节点列表,生成配置文件
> python update_proxy.py 订阅地址 --ps "01-中转-2x-流媒体全解锁" "02-中转-2X-流媒体全解锁" --config_name /tmp/c.json

## 测试配置文件是否正确
> v2ray test --config /tmp/c.json

## 启用配置文件进行测试
```

    sudo cp  /tmp/c.json /usr/local/etc/v2ray/config.json
    sudo systemctl restart v2ray
    echo "Restarted V2Ray service."

    sleep 1


    export http_proxy=http://192.168.1.30:10809
    export https_proxy=http://192.168.1.30:10809
 
    # 测试连接
    curl https://www.google.com
```

