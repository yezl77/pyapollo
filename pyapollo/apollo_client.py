# -*- coding: utf-8 -*-
import json
import logging
import threading
import time
import os
import requests
import yaml

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
consoleHandler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(consoleHandler)


class ApolloClient(object):
    def __init__(self):
        self.config_server_url = None
        self.app_id = None
        self.cluster = 'default'
        self.timeout = 65
        self.stopped = False
        self._stopping = False
        self._cache = {}
        self._notification_map = {'application': -1}
        self.env_local = True
        self.env_local_path = "/conf"
        self.ip = None
        pass

    def init_with_param(self, config_server_url=None,
                        app_id=None, cluster='default', timeout=65,
                        ip=None, env_local=True, local_path="/conf"):
        self.config_server_url = config_server_url
        self.app_id = app_id
        self.cluster = cluster
        self.timeout = timeout
        self.init_ip(ip)
        self.env_local = env_local
        self.env_local_path = local_path
        self.start()

    def init_with_conf(self, path="../conf/app.yaml"):
        ip = None
        try:
            with open(path, 'r') as f:
                y = yaml.load(f)
                for key in y.keys():
                    if key == 'config_server_url':
                        self.config_server_url = y[key]
                    elif key == 'app_id':
                        self.app_id = y[key]
                    elif key == 'cluster':
                        self.cluster = y[key]
                    elif key == 'timeout':
                        self.timeout = y[key]
                    elif key == 'ip':
                        ip = y[key]
                    elif key == 'env_local':
                        self.env_local = y[key]
                    elif key == 'env_local_path':
                        self.env_local_path = y[key]
        except Exception, e:
            print e
        self.init_ip(ip)
        self.start()
        time.sleep(1)  # 配置中心最多会有一秒的延时，

    def init_with_config(self, config):
        self.config_server_url = config.config_server_url
        self.app_id = config.app_id
        self.cluster = config.cluster
        self.timeout = config.timeout
        self.stopped = False
        self.init_ip(config.ip)
        self._stopping = False
        self._cache = {}
        self._notification_map = {'application': -1}
        self.env_local = config.env_local
        self.env_local_path = config.local_path
        self.start()

    def init_ip(self, ip):
        if ip:
            self.ip = ip
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
            self.ip = ip

    # get all value
    def get_config_by_namespace(self, namespace='application',
                                default_val=None):
        if namespace in self._cache:
            return self._cache[namespace]
        else:
            # self._enrol(namespace)    # 到底需不需要注册
            self._cached_http_get(namespace=namespace)
            if namespace in self._cache:
                return self._cache[namespace]
            else:
                if self.env_local:
                    self._local_file_get(namespace)
                    if namespace in self._cache:
                        return self._cache[namespace]
                return default_val

    # Main method
    def get_value(self, key, default_val=None, namespace='application'):
        self.get_config_by_namespace(namespace)
        if namespace in self._cache:
            if key in self._cache[namespace]:
                return self._cache[namespace][key]
            else:
                if self.env_local:
                    self._local_file_get(namespace)
                    if key in self._cache[namespace]:
                        return self._cache[namespace][key]
        return default_val

    # Start the long polling loop. Two modes are provided:
    # 1: thread mode (default), create a worker thread to do the loop.
    #  Call self.stop() to quit the loop
    # 2: eventlet mode (recommended), no need to call the .stop()
    # since it is async

    def start(self, func=None, namespace='application', use_eventlet=False,
              eventlet_monkey_patch=False, catch_signals=True):
        # First do a blocking long poll to populate the local cache,
        # otherwise we may get racing problems

        self._enrol(namespace)

        if self.config_server_url and self.app_id and self.cluster:
            if len(self._cache) == 0:
                self._long_poll()
            if use_eventlet:
                import eventlet
                if eventlet_monkey_patch:
                    eventlet.monkey_patch()
                eventlet.spawn(self._listener(func, namespace))
            else:
                if catch_signals:
                    import signal
                    signal.signal(signal.SIGINT, self._signal_handler)
                    signal.signal(signal.SIGTERM, self._signal_handler)
                    signal.signal(signal.SIGABRT, self._signal_handler)

                t = threading.Thread(target=self._listener,
                                     args=(func, namespace))
                t.start()
        else:
            if not self.config_server_url:
                logger.error("config_server_url is None")
            if not self.app_id:
                logger.error("app_id is None")
            if not self.cluster:
                logger.error("cluster is None")

    def stop(self):
        self._stopping = True
        logger.info("Stopping listener...")

    def _enrol(self, namespace):
        if namespace not in self._notification_map:
            self._notification_map[namespace] = -1
            logger.info(
                "Add namespace '%s' to local notification map", namespace)

        if namespace not in self._cache:
            self._cache[namespace] = {}
            logger.info(
                "Add namespace '%s' to local cache", namespace)

    def _cached_http_get(self, namespace='application'):
        url = '{}/configfiles/json/{}/{}/{}?ip={}'.format(
            self.config_server_url, self.app_id, self.cluster, namespace,
            self.ip)
        try:
            r = requests.get(url)
        except Exception, e:
            logger.warn(e)
        else:
            if r.ok:
                data = r.json()
                self._cache[namespace] = self._parse(data, namespace)

                logger.info(
                    'Updated local cache for namespace %s', namespace)

    def _uncached_http_get(self, namespace='application'):
        url = '{}/configs/{}/{}/{}?ip={}'.format(self.config_server_url,
                                                 self.app_id, self.cluster,
                                                 namespace, self.ip)
        try:
            r = requests.get(url)
        except Exception, e:
            logger.warn(e)
        else:
            if r.status_code == 200:
                data = r.json()
                self._cache[namespace] = self._parse(
                    data=data['configurations'],
                    namespace=namespace)
                self._local_file_download(namespace)
                logger.info(
                    'Updated local cache for namespace %s release key %s: %s',
                    namespace, data['releaseKey'],
                    repr(self._cache[namespace]))

    def _signal_handler(self, signal, frame):
        logger.info('You pressed Ctrl+C!')
        self._stopping = True

    def _long_poll(self):
        url = '{}/notifications/v2'.format(self.config_server_url)
        notifications = []
        for key in self._notification_map:
            notification_id = self._notification_map[key]
            notifications.append({
                'namespaceName': key,
                'notificationId': notification_id
            })
        try:
            r = requests.get(url=url, params={
                'appId': self.app_id,
                'cluster': self.cluster,
                'notifications': json.dumps(notifications, ensure_ascii=False)
            }, timeout=self.timeout)
        except Exception, e:
            logger.debug('Long polling returns Error:',
                         e)
            if self.env_local:
                for key in self._notification_map:
                    self._local_file_get(key)
            time.sleep(self.timeout)
        else:
            logger.debug('Long polling returns %d: url=%s',
                         r.status_code, r.request.url)

            if r.status_code == 304:
                # no change, loop
                logger.debug('No change, loop...')
                return False

            if r.status_code == 200:
                data = r.json()
                for entry in data:
                    ns = entry['namespaceName']
                    nid = entry['notificationId']
                    logger.info(
                        "%s has changes: notificationId=%d", ns, nid)

                    self._uncached_http_get(ns)
                    self._notification_map[ns] = nid
                return True
            else:
                if r.status_code == 400:
                    logger.warn('Bad Request!!!')
                elif r.status_code == 404:
                    logger.warn('Not Found!!!')
                elif r.status_code == 405:
                    logger.warn('Method Not Allowed!!!')
                elif r.status_code == 500:
                    logger.warn('Server Error,Sleep...')
                    time.sleep(self.timeout)
                return False

    def _listener(self, func, namespace):
        logger.info('Entering listener loop...')
        while not self._stopping:
            old_value = self._cache[namespace]
            old_id = self._notification_map[namespace]
            if self._long_poll():
                if old_id != self._notification_map[namespace]:
                    if func:
                        t = threading.Thread(target=func, args=(
                            old_value, self._cache[namespace]))
                        t.start()

        logger.info("Listener stopped!")
        self.stopped = True

    def _local_file_get(self, namespace='application'):
        if self.env_local:
            filepath = self.env_local_path + os.sep + self.app_id + os.sep + self.cluster + os.sep
            folder = os.path.exists(filepath)
            if not folder:
                logger.warn("local file not exits")
            else:
                try:
                    with open(os.getcwd() + os.sep + filepath + namespace,
                              'r') as f:
                        if namespace.endswith('.yaml'):
                            self._cache[namespace] = yaml.load(f)
                        elif namespace.endswith('.json'):
                            self._cache[namespace] = json.load(f)
                        else:
                            self._cache[namespace] = json.load(f)
                        self._enrol(namespace)
                except Exception, e:
                    logger.warn(e)

    def _local_file_download(self, namespace='application'):
        filepath = self.env_local_path + os.sep + self.app_id + os.sep + self.cluster + os.sep
        folder = os.path.exists(filepath)
        if not folder:
            os.makedirs(filepath)
        try:
            with open(os.getcwd() + os.sep + filepath + namespace, 'w+') as f:
                if namespace.endswith('.yaml'):
                    f.write(self._cache[namespace].encode('unicode-escape').decode('string_escape'))
                if namespace.endswith('.xml'):
                    f.write(self._cache[namespace].encode('unicode-escape').decode('string_escape'))
                if namespace.endswith('.json'):
                    json.dump(self._cache[namespace], f)
                else:
                    json.dump(self._cache[namespace], f)

        except Exception, e:
            logger.warn(e)

    def _parse(self, data, namespace):
        if namespace.endswith('.yaml'):
            return yaml.load(data['content'])
        if namespace.endswith('.json'):
            return json.loads(data['content'])
        if namespace.endswith('.xml'):
            return data['content']
        else:
            return data

#
# if __name__ == '__main__':
#     root = logging.getLogger()
#     root.setLevel(logging.DEBUG)
#
#     ch = logging.StreamHandler(sys.stdout)
#     ch.setLevel(logging.INFO)
#     formatter = logging.Formatter(
#         '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     ch.setFormatter(formatter)
#     root.addHandler(ch)
#
#     client = ApolloClient('pycrawler')
#     client.start()
#     if sys.version_info[0] < 3:
#         v = raw_input('Press any key to quit...')
#     else:
#         v = input('Press any key to quit...')
#
#     client.stop()
#     while not client.stopped:
#         pass
