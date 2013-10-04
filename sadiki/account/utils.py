# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from sadiki.account.plugins import plugins, AccountPlugin

__author__ = 'dmitry.sobolev'


def get_plugin_menu_items():
    result = {}
    for plugin in plugins:
        if not isinstance(plugin, AccountPlugin):
            raise AttributeError('Plugin object must be instance of AccountPlugin class')

        for url_name, name in plugin.get_menu_item().iteritems():
            url = reverse(url_name)
            result[url] = name

    return result