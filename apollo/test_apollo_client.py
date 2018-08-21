# -*- coding: utf-8 -*-
import unittest
import client
import conf

def update_on_callback(old_value, update_value):
    print "更新了，回调======"
    print "old_value:", old_value
    print "update_value:", update_value
    print "============="


class TestApolloClient(unittest.TestCase):

    # 通过配置对象启动
    def test_init1(self):
        apolloclient = client.ApolloClient()
        config = conf.ApolloConfig(app_id="app-apollo-demo", cluster="default",
                                   config_server_url="http://127.0.0.1:8080/")
        apolloclient.init_with_config(config)

        print('\n'.join(['%s:%s' % item for item in apolloclient.__dict__.items()]))

    # 通过配置参数启动
    def test_init2(self):
        apolloclient = client.ApolloClient()
        apolloclient.init_with_param(
            config_server_url="http://120.131.9.219:8080/",
            app_id="demo", cluster="alpha", timeout=62, env_local=False,
        )
        print('\n'.join(['%s:%s' % item for item in apolloclient.__dict__.items()]))

    # 通过配置文件启动
    def test_init3(self):
        apolloclient = client.ApolloClient()
        apolloclient.init_with_conf()
        print('\n'.join(['%s:%s' % item for item in apolloclient.__dict__.items()]))

    # 获取指定namespace=mongodb.yaml的对象
    def test_get_config_by_namespace(self):
        apolloclient = client.ApolloClient()
        config = conf.ApolloConfig(app_id="app-apollo-demo", cluster="default",
                                   config_server_url="http://127.0.0.1:8080/")
        apolloclient.init_with_config(config)
        all_value, source_type = apolloclient.get_config_by_namespace(namespace='testyaml.yaml')
        self.assertEqual(source_type, conf.SourceType.REMOTE, "test_get_config_by_namespace")


    # 获取指定namespace='redis.json'的对象
    def test_get_config_by_namespace1(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        all_value, source_type = apollo_client.get_config_by_namespace(namespace='redis.json')
        print all_value
        self.assertEquals(all_value, None)

    # 获取指定namespace默认application的对象
    def test_get_config_by_namespace2(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        all_value, source_type = apollo_client.get_config_by_namespace()
        print all_value

    # 获取指定namespace=testyaml.yaml的对象，配置中心不存在，本地存在
    def test_get_config_by_namespace3(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        all_value, source_type = apollo_client.get_config_by_namespace(namespace='testyaml.yaml')
        print all_value

    # 获取指定namespace=testyaml.yaml的对象，配置中心和本地都不不存在
    def test_get_config_by_namespace4(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        all_value, source_type = apollo_client.get_config_by_namespace(namespace='mongodb2.yaml')
        print all_value

    # 测试获取键对应的值，默认namespace=application,key='timeout'
    def test_get_value(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        timeout, source_type = apollo_client.get_value(key='timeout')
        self.assertEquals(timeout, 85)

    # 测试获取键对应的值，namespace=redis.json, key='path'
    def test_get_value0(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        path, source_type = apollo_client.get_value(namespace="redis.json", key='path')
        print path
        self.assertEquals(path, "/usr/alphatest")

    # 测试获取键对应的值，namespace=mongodb.yaml,key="name"
    def test_get_value1(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        name, source_type = apollo_client.get_value(namespace='mongodb.yaml', key="name")
        print name

    # 测试获取键对应的值，namespace=testyaml.yaml,key="name"，配置中心不存在，
    # 本地存在
    def test_get_value2(self):
        apolloclient = client.ApolloClient()
        config = conf.ApolloConfig(app_id="app-apollo-demo", cluster="default",
                                   config_server_url="http://127.0.0.1:8080/")
        apolloclient.init_with_config(config)
        name, source_type = apolloclient.get_config_by_namespace(namespace='testyaml.yaml')
        print name,source_type

    # 测试获取键对应的值，namespace=testyaml.yaml,key="name"，配置中心不存在，
    # 本地存在，但是key不存在
    def test_get_value3(self):
        apolloclient = client.ApolloClient()
        config = conf.ApolloConfig(app_id="app-apollo-demo", cluster="default",
                                   config_server_url="http://127.0.0.1:8080/")
        apolloclient.init_with_config(config)
        name, source_type = apolloclient.get_value(namespace='testyaml.yaml', key="name",
                                default_val="默认值+")
        self.assertEqual(name,"root", "测试获取key成功")

    # 启动监听回调，namespace="mongodb.yaml"
    def test_start(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        apollo_client.start_listen(namespace="mongodb.yaml", func=update_on_callback)

    # 启动监听回调2，namespace="redis.json"
    def test_start1(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        apollo_client.start_listen(namespace="redis.json", func=update_on_callback)

    # 启动监听回调，默认namespace=application
    def test_start2(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        apollo_client.start_listen(func=update_on_callback)

    # 启动监听回调2，namespace="testjson.json"，配置中心不存在，本地也不存在
    def test_start3(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        apollo_client.start_listen(namespace="testjson.json", func=update_on_callback)

    # 启动监听回调2，namespace="testyaml.yaml"，配置中心不存在，本地存在
    def test_start4(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        apollo_client.start_listen(namespace="testyaml.yaml", func=update_on_callback)

    # 关闭监听回调
    def test_stop(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        print apollo_client._config_server_url
        apollo_client.start_listen(namespace="mongodb.yaml", func=update_on_callback)
        apollo_client.stop()

    # 启动监听回调2，namespace="testyaml.yaml"，key="timeout"
    def test_start_key(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        apollo_client.start_listen(namespace="testyaml.yaml", key="timeout",
                            func=update_on_callback)

    # 启动监听回调2，namespace="testyaml.yaml"，key="age" 一开始不存在，后来增加
    def test_start_key1(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        apollo_client.start_listen(namespace="testyaml.yaml", key="age",
                            func=update_on_callback)

    # 启动监听回调2，namespace="testyaml.yaml"，key="age" 一开始存在，后来删除
    def test_start_key2(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        apollo_client.start_listen(namespace="testyaml.yaml", key="age",
                            func=update_on_callback)

    def test_source_type(self):
        apollo_client = client.ApolloClient()
        apollo_client.init_with_conf()
        name, source_type = apollo_client.get_value(namespace='testyaml.yaml', key="name")
        print source_type
        print name
        self.assertEqual(source_type, conf.SourceType.REMOTE, "test_source_type成功")
