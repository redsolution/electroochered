# -*- coding: utf-8 -*-

plugins = []


class AccountPlugin:
    def __init__(self):
        pass

    def get_urls(self):
        raise NotImplementedError

    def get_menu_item(self):
        raise NotImplementedError


def add_plugin(plugin):
    if not isinstance(plugin, AccountPlugin):
        raise AttributeError("Plugin must be instance of AccountPlugin class")

    plugins.append(plugin)
