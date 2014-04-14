# -*- coding: utf-8 -*- 
from django.conf.urls.defaults import patterns, url, include
from django.contrib import admin
from .views import Frontpage, sadiki_json, registration, queue, search, import_params

urlpatterns = patterns('',
    url(r'^$', Frontpage.as_view(), name='frontpage'),
    url(r'^api/sadiki.json$', sadiki_json, name='sadiki_json'),
    url(r'^registration/$', registration, name=u'anonym_registration'),
    url(r'^queue/$', queue, name=u'anonym_queue'),
    url(r'^requestion_search/$', search, name=u'anonym_requestion_search'),
    url(r'^import_params/$', import_params, name='import_params_json'),

    url(r'^admin/', include(admin.site.urls), name="default_admin"),
)
