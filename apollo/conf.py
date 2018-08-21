# -*- coding: utf-8 -*-
from enum import Enum


SourceType = Enum('SourceType', ('REMOTE', 'LOCAL', 'DEFAULT'))


class ApolloConfig(object):
    def __init__(self, config_server_url, app_id, cluster="default", timeout=65,
                 ip=None, env_local=True, local_path="conf/"):
        self.config_server_url = config_server_url
        self.app_id = app_id
        self.cluster = cluster
        self.timeout = timeout
        self.ip = ip
        self.env_local = env_local
        self.local_path = local_path


class Config(object):
    def __init__(self, config, source_type=SourceType.REMOTE):
        self._config = config
        self._source_type = source_type

    def get_config(self):
        return self._config

    def get_source_type(self):
        return self._source_type
