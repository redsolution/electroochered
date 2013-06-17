# -*- coding: utf-8 -*- 
from django.conf.urls.defaults import patterns, url
from .views import Frontpage, Settings, sadiki_json, registration, queue, search

urlpatterns = patterns('',
    url(r'^$', Frontpage.as_view(), name='frontpage'),
    url(r'^settings/$', Settings.as_view(), name='settings'),
    url(r'^api/sadiki.json$', sadiki_json, name='sadiki_json'),
    url(r'^registration/$', registration, name=u'anonym_registration'),
    url(r'^queue/$', queue, name=u'anonym_queue'),
    url(r'^requestion_search/$', search, name=u'anonym_requestion_search'),
)
