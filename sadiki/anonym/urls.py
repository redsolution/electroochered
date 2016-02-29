# -*- coding: utf-8 -*- 
from django.conf.urls import url
from sadiki.anonym.views import Frontpage, SadikInfo, SadikList, SadikiMap


urlpatterns = [
    url(r'^$', Frontpage.as_view(), name=u'anonym_frontpage'),
    url(r'^sadik/$', SadikList.as_view(),
        name=u'sadik_list'),
    url(r'^sadik/(?P<sadik_id>\d{1,7})/$', SadikInfo.as_view(),
        name=u'sadik_info'),
    url(r'^map/', SadikiMap.as_view(), 
    	name='sadiki_map'),
]
