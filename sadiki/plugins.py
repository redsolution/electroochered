# -*- coding: utf-8 -*-

plugins = []


class SadikiPlugin(object):

    def get_urls(self):
        raise NotImplementedError


def add_plugin(plugin):
    if not isinstance(plugin, SadikiPlugin):
        raise AttributeError("Plugin must be instance of SadikiPlugin class")

    plugins.append(plugin)
