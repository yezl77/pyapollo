# -*- coding: utf-8 -*-
import json
import logging
import os
import requests
import yaml

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.WARN)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
consoleHandler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(consoleHandler)


# 发送带缓存的Http请求
def cached_http_get(config_server_url, app_id, cluster, ip,
                    namespace='application'):
    url = '{}/configfiles/json/{}/{}/{}?ip={}'.format(
        config_server_url, app_id, cluster, namespace,
        ip)
    try:
        r = requests.get(url)
    except Exception, e:
        logger.warn("cached_http_get: %s", e)
    else:
        if r.ok:
            data = r.json()
            return _parse(data, namespace), True
    return None, False


# 发送不带缓存的Http请求
def uncached_http_get(config_server_url, app_id, cluster, ip,
                      namespace='application'):
    url = '{}/configs/{}/{}/{}?ip={}'.format(config_server_url,
                                             app_id, cluster,
                                             namespace, ip)
    try:
        r = requests.get(url)
    except Exception, e:
        logger.warn("uncached_http_get: %s", e)
    else:
        if r.status_code == 200:
            data = r.json()
            if 'configurations' in data:
                data = data['configurations']
            else:
                logger.warn("key configurations not exit,apollo info error")
            return _parse(data, namespace=namespace), True
    return None, False


# 请求配置更新推送 有更新，返回True,否则返回False
def get_server_config_update(config_server_url, notifications, app_id, cluster,
                             timeout):
    url = '{}/notifications/v2'.format(config_server_url)
    try:
        r = requests.get(url=url, params={
            'appId': app_id,
            'cluster': cluster,
            'notifications': json.dumps(notifications, ensure_ascii=False)
        }, timeout=timeout)
    except Exception, e:
        logger.warn('get_server_config_update returns Error: %s', e)
    else:
        logger.info('get_server_config_update returns %d: url=%s',
                    r.status_code, r.request.url)

        if r.status_code == 304:
            # no change, loop
            logger.info('No change, loop...')

        if r.status_code == 200:
            data = r.json()
            return data, True
        else:
            if r.status_code == 400:
                logger.warn('Bad Request!!!')
            elif r.status_code == 404:
                logger.warn('Not Found!!!')
            elif r.status_code == 405:
                logger.warn('Method Not Allowed!!!')
            elif r.status_code == 500:
                logger.warn('Server Error,Sleep...')
    return None, False


# 缓存配置对象到本地
def dump_to_local(filepath, config, namespace='application'):
    folder = os.path.exists(filepath)
    if not folder:
        os.makedirs(filepath)
    try:
        with open(filepath + namespace, 'w+') as f:
            if namespace.endswith('.yaml'):
                yaml.dump(config, f)
            else:
                json.dump(config, f)

    except Exception, e:
        logger.warn("dump_to_local: %s", e)


# 从本地获取配置
def get_with_local(filepath, namespace='application'):
    if not os.path.exists(filepath):
        logger.warn("local file not exits")
    else:
        try:
            with open(filepath, 'r') as f:
                if namespace.endswith('.yaml'):
                    return yaml.load(f), True
                else:
                    return json.load(f), True
        except Exception, e:
            logger.warn("get_with_local: %s", e)

    return None, False


def _parse(data, namespace):
    if namespace.endswith('.yaml'):
        if 'content' in data:
            return yaml.load(data['content'])
    else:
        if 'content' in data:
            return json.loads(data['content'])
    return data
