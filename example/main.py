# -*- coding: utf-8 -*-

from apollo import client
from apollo import conf


def update_oncallback(oldvalue, updatevalue):
    print ">>>>>>>>>>>>>"
    print "oldvalue:", oldvalue
    print "updatevalue:", updatevalue
    print "<<<<<<<<<<<<<"


if __name__ == "__main__":
    client = client.ApolloClient()
    client.init_with_conf(path="app.yaml")

    client.start_listen(namespace="testApp.yaml",
                        func=update_oncallback)

    # value, source_type = client.get_value(namespace="testyaml.yaml",
    #                                       key="spouse",
    #                                       default_val="default_value")
    # print source_type
    # if source_type == conf.SourceType.REMOTE:
    #     print "from REMOTE"
    # print value
    # if "info" in value:
    #     print value["info"]
    #
    value = client.get_config_by_namespace(namespace="testApp.yaml",
                                           default_val="default_value")
    print value
