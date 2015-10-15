# -*- coding: utf-8 -*- 
from django.conf.urls import url, include
from django.contrib import admin
from .views import Frontpage, sadiki_json, registration, queue, search, import_params, \
    GetCoordsFromAddress
from sadiki.anonym.views import QueueMap

urlpatterns = [
    url(r'^$', Frontpage.as_view(), name='frontpage'),
    url(r'^api/sadiki.json$', sadiki_json, name='sadiki_json'),
    url(r'^registration/$', registration, name=u'anonym_registration'),
    url(r'^queue/$', queue, name=u'anonym_queue'),
    url(r'^queuemap/$', QueueMap.as_view(), name=u'queue_map'),
    url(r'^get_coords/$',
        GetCoordsFromAddress.as_view(), name='get_coords_from_address'),
    url(r'^requestion_search/$', search, name=u'anonym_requestion_search'),
    url(r'^import_params/$', import_params, name='import_params_json'),

    url(r'^admin/', include(admin.site.urls), name="default_admin"),
]
