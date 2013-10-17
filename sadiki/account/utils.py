# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from sadiki.account.plugins import plugins, AccountPlugin

__author__ = 'dmitry.sobolev'


def get_plugin_menu_items():
    result = {}
    for plugin in plugins:
        try:
            if not isinstance(plugin, AccountPlugin):
                raise AttributeError('Plugin object must be instance of AccountPlugin class')

            for url_name, name in plugin.get_menu_item().iteritems():
                url = reverse(url_name)
                result[url] = name
        except NotImplementedError:
            continue

    return result


def get_profile_additions():
    result = []

    for plugin in plugins:
        try:
            if not isinstance(plugin, AccountPlugin):
                raise AttributeError('Plugin object must be instance of AccountPlugin class')

            if not isinstance(plugin.get_profile_addition(), (str, unicode)):
                raise AttributeError('Method \'get_profile_addition\' of plugin must return string or unicode object')

            result.append(plugin.get_profile_addition())
        except NotImplementedError:
            continue

    return result