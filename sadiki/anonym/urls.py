# -*- coding: utf-8 -*- 
from django.conf.urls.defaults import patterns, url
from sadiki.anonym.views import Frontpage, SadikInfo, SadikList


urlpatterns = patterns('',
    url(r'^$', Frontpage.as_view(), name=u'anonym_frontpage'),
    url(r'^sadik/$', SadikList.as_view(),
        name=u'sadik_list'),
    url(r'^sadik/(?P<sadik_id>\d{1,7})/$', SadikInfo.as_view(),
        name=u'sadik_info'),
)
