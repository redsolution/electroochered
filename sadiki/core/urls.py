# -*- coding: utf-8 -*- 
from django.conf.urls.defaults import patterns, url
from .views import Frontpage, Settings, sadiki_json

urlpatterns = patterns('',
    url(r'^$', Frontpage.as_view(), name='frontpage'),
    url(r'^settings/$', Settings.as_view(), name='settings'),
    url(r'^api/sadiki.json$', sadiki_json, name='sadiki_json'),
)
