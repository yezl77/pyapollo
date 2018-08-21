# 阿波罗配置中心python客户端

## 功能

* 多 namespace 支持
* 容错，本地缓存
* 灰度配置
* 适配多种配置格式（.yaml  .json  .properties）
* 粒度可达到namespace和key

## 依赖

python 2.7 

## 安装

```sh
   git clone下来后进入目录下，打开控制台，输入pip install .  安装到本地
```

## 使用

### 使用 app.yaml 配置文件启动

```python
from apollo import client

client = client.ApolloClient()
client.init_with_conf(path="app.yaml")
```

### 使用自定义配置启动

```python
from apollo import client

class Config():
    def __init__(self, config_server_url, app_id, cluster, timeout=65,
                          ip=None, env_local=True, local_path="conf"):
        self.config_server_url = config_server_url
        self.app_id = app_id
        self.cluster = cluster
        self.timeout = timeout
        self.ip = ip
        self.env_local = env_local
        self.local_path = local_path
        
        
client = ApolloClient()
config=Config(config_server_url="http://127.0.0.1:8081/"，
              app_id="demo", cluster="alpha")
client.init_with_config(config)
```

### 使用 配置参数启动

```python
from apollo import client

client = ApolloClient()
client.init_with_param(
  config_server_url="http://120.131.9.219:8080/",
  app_id="demo", cluster="alpha", timeout=62, env_local=False,)
```

### 监听配置更新

```python
# 更新回调
def update_oncallback(oldvalue, updatevalue):   
    print ">>>>>>>>>>>>>"
    print "oldvalue:", oldvalue
    print "updatevalue:", updatevalue
    print "<<<<<<<<<<<<<"

# 默认监听 namespace=application , key=apollo  只提供对第一级的key的监听
 client.start_listen(key="apollo", func=update_oncallback)
  
# 监听 namespace=testyaml.yaml , key=children   只提供对第一级的key的监听
 client.start_listen(namespace="testyaml.yaml", key="children", func=update_oncallback)
    
# 监听 namespace=testyaml.yaml , 不传入key, 则监听整个namespace配置的更新
 client.start_listen(namespace="testyaml.yaml", func=update_oncallback)
  
# 监听 namespace=testjson.json , key=path   只提供对第一级的key的监听
client.start_listen(namespace="testjson.json", key="path", func=update_oncallback)
  
```

### 获取配置

```python
# 获取默认 namespace=application , key=apollo  默认返回值=default_value
value, source_type = client.get_value(key="apollo", default_val="default_value")
print value
if source_type == conf.SourceType.REMOTE:
    print "from REMOTE"

# 获取 namespace=testyaml.yaml , key=spouse  默认返回值=yemp
value, source_type = client.get_value(namespace="testyaml.yaml", key="spouse",
                             default_val="default_value")
print value
if "info" in value:       # 如果返回的是dict，可按需要获取下一级的key的值，
    print value["info"]  
    
# 获取整个namespace的值
value = client.get_config_by_namespace(namespace="testyaml.yaml",
                                           default_val="default_value")
print value
```

注：新建项目的默认application如果没有第一次发布，那么就会阻塞客户端对其他namespace的配置的更新监听和查询

## 许可

apollo 使用 MIT 许可