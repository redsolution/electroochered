# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from sadiki.account.plugins import AccountPlugin

plugins = []


def add_plugin(plugin):
    if not isinstance(plugin, AccountPlugin):
        raise AttributeError("Plugin must be instance of AccountPlugin class")

    plugins.append(plugin)


def get_operator_plugin_menu_items(profile_id):
    result = {}
    for plugin in plugins:
        if not isinstance(plugin, AccountPlugin):
            raise AttributeError('Plugin object must be instance of AccountPlugin class')

        for url_name, name in plugin.get_menu_item().iteritems():
            url = reverse(url_name, kwargs={'profile_id': profile_id})
            result[url] = name

    return result
