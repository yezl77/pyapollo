# -*- coding: utf-8 -*-
import logging
import threading
import os
import yaml
import utillib
import conf

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.WARN)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
consoleHandler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(consoleHandler)


class ApolloClient(object):
    def __init__(self):
        self._config_server_url = None
        self._app_id = None
        self._cluster = 'default'
        self._timeout = 65
        self._stopped = False
        self._stopping = False
        self._cache = {}
        self._notification_map = {'application': -1}
        self._env_local = False
        self._env_local_path = "/conf"
        self._ip = None
        self._init_ip()
        self._catch_lock = threading.Lock()
        self._notification_map_lock = threading.Lock()
        self._stopping_lock = threading.Lock()
        self._stopped_lock = threading.Lock()

    def _check_param(self):
        if not self._cluster:
            self._cluster = 'default'
        if not self._timeout:
            self._timeout = 65
        if not self._env_local:
            self._env_local = False
        if not self._env_local_path:
            self._env_local_path = "/conf"

    def init_with_param(self, config_server_url,
                        app_id, cluster='default', timeout=65,
                        ip=None, env_local=True, local_path="/conf"):
        self._config_server_url = config_server_url
        self._app_id = app_id
        self._cluster = cluster
        self._timeout = timeout
        self._init_ip(ip)
        self._env_local = env_local
        self._env_local_path = local_path
        self._start()

    def init_with_conf(self, path="app.yaml"):
        try:
            with open(path, 'r') as f:
                y = yaml.load(f)
                for key in y.keys():
                    if key == 'config_server_url':
                        self._config_server_url = y[key]
                    elif key == 'app_id':
                        self._app_id = y[key]
                    elif key == 'cluster':
                        self._cluster = y[key]
                    elif key == 'timeout':
                        self._timeout = y[key]
                    elif key == 'ip':
                        ip = y[key]
                        self._init_ip(ip)
                    elif key == 'env_local':
                        self._env_local = y[key]
                    elif key == 'env_local_path':
                        self._env_local_path = y[key]
        except Exception, e:
            logger.error("init_with_conf open app.yaml:", e)
        self._start()

    def init_with_config(self, config):
        self._config_server_url = config.config_server_url
        self._app_id = config.app_id
        self._cluster = config.cluster
        self._timeout = config.timeout
        self._init_ip(config.ip)
        self._env_local = config.env_local
        self._env_local_path = config.local_path
        self._start()

    def _init_ip(self, ip=None):
        if ip:
            self._ip = ip
        else:
            import socket
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 53))
                ip = s.getsockname()[0]
            except Exception, e:
                logger.error(e)
                ip = "0.0.0.0"
            finally:
                s.close()
            self._ip = ip

    # get all value
    def get_config_by_namespace(self, namespace='application',
                                default_val=None):
        config, source_type, ok = self._get_catch(namespace)
        if ok:
            return config, source_type
        else:
            config, ok = utillib.cached_http_get(self._config_server_url,
                                                 self._app_id, self._cluster,
                                                 self._ip, namespace)
            if ok:
                self._set_catch(namespace, config, conf.SourceType.REMOTE)
                return config, conf.SourceType.REMOTE
            else:
                if self._env_local:
                    config, ok = self._get_with_local(namespace)
                    if ok:
                        self._set_catch(namespace, config,
                                        conf.SourceType.LOCAL)
                        return config, conf.SourceType.LOCAL
                return default_val, conf.SourceType.DEFAULT

    # Main method
    def get_value(self, key, default_val=None, namespace='application'):
        self.get_config_by_namespace(namespace)
        config, source_type, ok = self._get_catch(namespace)
        if ok:
            if key in config:
                return config[key], source_type
            else:
                if self._env_local:
                    config, ok = self._get_with_local(namespace)
                    if ok:
                        if key in config:
                            self._set_catch(namespace, config,
                                            conf.SourceType.LOCAL)
                            return config[key], conf.SourceType.LOCAL
        return default_val, conf.SourceType.DEFAULT

    # 开启线程 同步缓存
    def _start(self):
        self._check_param()
        self.start_listen()

    # 监听回调
    def start_listen(self, func=None, namespace='application', key=None,
                     use_eventlet=False,
                     eventlet_monkey_patch=False, catch_signals=True):
        self._enrol(namespace)
        if self._config_server_url and self._app_id and self._cluster:
            if self._get_catch_len() == 0:
                self._long_poll()
            if use_eventlet:
                import eventlet
                if eventlet_monkey_patch:
                    eventlet.monkey_patch()
                eventlet.spawn(self._listener(func, namespace, key))
            else:
                if catch_signals:
                    import signal
                    signal.signal(signal.SIGINT, self._signal_handler)
                    signal.signal(signal.SIGTERM, self._signal_handler)
                    signal.signal(signal.SIGABRT, self._signal_handler)

                t = threading.Thread(target=self._listener,
                                     args=(func, namespace, key))
                t.start()
        else:
            if not self._config_server_url:
                logger.error("config_server_url is None")
            if not self._app_id:
                logger.error("app_id is None")
            if not self._cluster:
                logger.error("cluster is None")

        # time.sleep(1)  # 配置中心拉取到本地缓存最多会有一秒的延时

    def stop(self):

        self._set_stopping(True)
        logger.info("Stopping listener...")

    def _get_catch(self, namespace):
        catch, source_type, flag = None, conf.SourceType.REMOTE, False
        self._catch_lock.acquire()
        if namespace in self._cache:
            catch, flag = self._cache[namespace].get_config(), True
            source_type = self._cache[namespace].get_source_type()
        self._catch_lock.release()
        return catch, source_type, flag

    def _get_catch_len(self):
        self._catch_lock.acquire()
        length = len(self._cache)
        self._catch_lock.release()
        return length

    def _set_catch(self, namespace, catch, source_type):
        self._catch_lock.acquire()
        self._cache[namespace] = conf.Config(catch, source_type)
        self._catch_lock.release()

    def _get_notification_map(self, namespace):
        notification_id = -1
        self._notification_map_lock.acquire()
        if namespace in self._notification_map:
            notification_id = self._notification_map[namespace]
        else:
            self._notification_map[namespace] = notification_id
        self._notification_map_lock.release()
        return notification_id

    def _set_notification_map(self, namespace, notification_id):
        self._notification_map_lock.acquire()
        self._notification_map[namespace] = notification_id
        self._notification_map_lock.release()

    def _get_notifications(self):
        notifications = []
        self._notification_map_lock.acquire()
        for key in self._notification_map:
            notification_id = self._notification_map[key]
            notifications.append({
                'namespaceName': key,
                'notificationId': notification_id
            })
        self._notification_map_lock.release()
        return notifications

    def _set_stopping(self, flag):
        self._stopping_lock.acquire()
        self._stopping = flag
        self._stopping_lock.release()

    def _get_stopping(self):
        flag = False
        self._stopping_lock.acquire()
        flag = self._stopping
        self._stopping_lock.release()
        return flag

    def _set_stopped(self, flag):
        self._stopped_lock.acquire()
        self._stopped = flag
        self._stopped_lock.release()

    def _get_stopped(self):
        flag = False
        self._stopped_lock.acquire()
        flag = self._stopped
        self._stopped_lock.release()
        return flag

    def _signal_handler(self, signal, frame):
        logger.info('You pressed Ctrl+C!')
        self._set_stopping(True)

    # 注册添加到更新监听队列
    def _enrol(self, namespace):
        self._get_notification_map(namespace)

    # 同步读取配置中心到缓存和本地
    def _sync_catch_local(self, namespace='application'):
        config, ok = utillib.uncached_http_get(self._config_server_url,
                                               self._app_id, self._cluster,
                                               self._ip, namespace=namespace)
        if ok:
            self._set_catch(namespace, config, conf.SourceType.REMOTE)
            filepath = self._env_local_path + os.sep + self._app_id + os.sep + \
                       self._cluster + os.sep
            if self._env_local:
                utillib.dump_to_local(filepath=filepath, config=config,
                                      namespace=namespace)

    # 长轮询
    def _long_poll(self):
        notifications = self._get_notifications()
        data, ok = utillib.get_server_config_update(
            config_server_url=self._config_server_url,
            notifications=notifications, app_id=self._app_id,
            cluster=self._cluster, timeout=self._timeout)
        if ok:
            for entry in data:
                if 'namespaceName' in entry and 'notificationId' in entry:
                    ns = entry['namespaceName']
                    nid = entry['notificationId']
                    self._sync_catch_local(ns)
                    self._set_notification_map(ns, nid)
                else:
                    logger.warn("key namespaceName notificationId not exit,"
                                "apollo info error")
        return ok

    def _listener(self, func, namespace, key):
        logger.info('Entering listener loop...')

        while not self._get_stopping():
            old_value, _, old_value_ok = self._get_catch(namespace)
            old_id = self._get_notification_map(namespace)
            if self._long_poll():
                self._callback(func, namespace, key, old_value, old_value_ok,
                               old_id)

        logger.info("Listener stopped!")
        self._set_stopped(True)

    def _callback(self, func, namespace, key, old_value, old_value_ok, old_id):
        call_old = None
        call_new = None
        call_flag = False
        if func:  # 判断是否有回调
            new_id = self._get_notification_map(namespace)
            if old_id != new_id:  # id不相等，有更新
                new_value, _, new_value_ok = self._get_catch(namespace)
                if key:
                    if old_value_ok:
                        if key in old_value:
                            call_old, call_flag = old_value[key], True
                    if new_value_ok:
                        if key in new_value:
                            call_new, call_flag = new_value[key], True
                else:
                    call_old = old_value
                    call_new = new_value
                    call_flag = True
        if call_flag:
            if cmp(call_old, call_new) is not 0:
                t = threading.Thread(target=func, args=(
                    call_old, call_new))
                t.start()

    def _get_with_local(self, namespace='application'):
        filepath = self._env_local_path + os.sep + \
                   self._app_id + os.sep + self._cluster + os.sep + namespace
        return utillib.get_with_local(filepath,
                                      namespace=namespace)
