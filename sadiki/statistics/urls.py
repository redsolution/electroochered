# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url
from sadiki.statistics.views import WaitTimeStatistics, RequestionsMap, requestions_coords_json
from django.conf import settings

urlpatterns = patterns('',
    url('^wait_time_statistics/$', WaitTimeStatistics.as_view(),
        name='wait_time_statistics'),

    url(r'^requestions_coords.json$', requestions_coords_json, name='requestions_coords_json'),
)

if settings.SHOW_REQUESTIONS_MAP:
    urlpatterns += patterns('',
        url('^requestions_map/$', RequestionsMap.as_view(),
            name='requestions_map'),)