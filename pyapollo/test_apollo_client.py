# -*- coding: utf-8 -*-
import unittest

from apollo_client import ApolloClient


class Config():
    def __init__(self, config_server_url, app_id, cluster, timeout=65, ip=None,
                 env_local=True, local_path="conf"):
        self.config_server_url = config_server_url
        self.app_id = app_id
        self.cluster = cluster
        self.timeout = timeout
        self.ip = ip
        self.env_local = env_local
        self.local_path = local_path


def update_oncallback(updatevalue, oldvalue):
    print "更新了，回调======"
    print oldvalue
    print updatevalue
    print "============="


class TestApolloClient(unittest.TestCase):

    # 通过配置对象启动
    def test_init1(self):
        client = ApolloClient()
        client.init_with_config(Config(app_id="demo", cluster="alpha",
                                       config_server_url="localhost:8080/"))
        print('\n'.join(['%s:%s' % item for item in client.__dict__.items()]))

    # 通过配置参数启动
    def test_init2(self):
        client = ApolloClient()
        client.init_with_param(
            config_server_url="localhost:8080/",
            app_id="demo", cluster="alpha",timeout=62,env_local=False,
                               )
        print('\n'.join(['%s:%s' % item for item in client.__dict__.items()]))

    # 通过配置文件启动
    def test_init3(self):
        client = ApolloClient()
        client.init_with_conf()
        print('\n'.join(['%s:%s' % item for item in client.__dict__.items()]))

    # 获取指定namespace=mongodb.yaml的对象
    def test_get_config_by_namespace(self):
        client = ApolloClient()
        client.init_with_conf()
        all_value = client.get_config_by_namespace(namespace='mongodb.yaml')
        print all_value

    # 获取指定namespace='redis.json'的对象
    def test_get_config_by_namespace1(self):
        client = ApolloClient()
        client.init_with_conf()
        all_value = client.get_config_by_namespace(namespace='redis.json')
        print all_value
        self.assertEquals(all_value, {u'info': {u'timeout': 60, u'size': 1024}, u'path': u'/usr/alphatest', u'enabled': True})


    # 获取指定namespace默认application的对象
    def test_get_config_by_namespace2(self):
        client = ApolloClient()
        client.init_with_conf()
        all_value = client.get_config_by_namespace()
        print all_value

    # 获取指定namespace=mongodb1.yaml的对象，配置中心不存在，本地存在
    def test_get_config_by_namespace3(self):
        client = ApolloClient()
        client.init_with_conf()
        all_value = client.get_config_by_namespace(namespace='mongodb1.yaml')
        print all_value

    # 获取指定namespace=mongodb1.yaml的对象，配置中心和本地都不不存在
    def test_get_config_by_namespace4(self):
        client = ApolloClient()
        client.init_with_conf()
        all_value = client.get_config_by_namespace(namespace='mongodb2.yaml')
        print all_value

    # 测试获取键对应的值，默认namespace=application,key='timeout'
    def test_get_value(self):
        client = ApolloClient()
        client.init_with_conf()
        timeout = client.get_value(key='timeout')
        self.assertEquals(timeout, 85)

    # 测试获取键对应的值，namespace=redis.json, key='path'
    def test_get_value0(self):
        client = ApolloClient()
        client.init_with_conf()
        path = client.get_value(namespace="redis.json", key='path')
        print path
        self.assertEquals(path, "/usr/alphatest")

    # 测试获取键对应的值，namespace=mongodb.yaml,key="name"
    def test_get_value1(self):
        client = ApolloClient()
        client.init_with_conf()
        name = client.get_value(namespace='mongodb.yaml', key="name")
        print name

    # 测试获取键对应的值，namespace=mongodb1.yaml,key="name"，配置中心不存在，本地存在
    def test_get_value2(self):
        client = ApolloClient()
        client.init_with_conf()
        name = client.get_value(namespace='mongodb1.yaml', key="name")
        print name

    # 测试获取键对应的值，namespace=mongodb1.yaml,key="name"，配置中心不存在，本地存在，但是key不存在
    def test_get_value3(self):
        client = ApolloClient()
        client.init_with_conf()
        name = client.get_value(namespace='mongodb1.yaml', key="name2",default_val="默认值+")
        print name

    # 启动监听回调，namespace="mongodb.yaml"
    def test_start(self):
        client = ApolloClient()
        client.init_with_conf()
        client.start(namespace="mongodb.yaml", func=update_oncallback)

    # 启动监听回调2，namespace="redis.json"
    def test_start1(self):
        client = ApolloClient()
        client.init_with_conf()
        client.start(namespace="redis.json", func=update_oncallback)

    # 启动监听回调，默认namespace=application
    def test_start2(self):
        client = ApolloClient()
        client.init_with_conf()
        client.start(func=update_oncallback)

    # 启动监听回调2，namespace="redis1.json"，配置中心不存在，本地也不存在
    def test_start3(self):
        client = ApolloClient()
        client.init_with_conf()
        client.start(namespace="redis1.json", func=update_oncallback)

    # 启动监听回调2，namespace="redis1.json"，配置中心不存在，本地存在
    def test_start4(self):
        client = ApolloClient()
        client.init_with_conf()
        client.start(namespace="mongodb1.yaml", func=update_oncallback)

    # 关闭监听回调
    def test_stop(self):
        client = ApolloClient()
        client.init_with_conf()
        print client.config_server_url
        client.start(namespace="mongodb.yaml", func=update_oncallback)
        client.stop()






