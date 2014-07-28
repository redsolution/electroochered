# -*- coding: utf-8 -*- 
from django.conf.urls import patterns, url, include

from sadiki.api.views import get_distributions, get_distribution, get_child

urlpatterns = patterns('',
    url(r'^get_distributions/$', get_distributions),
    url(r'^get_distribution/(?P<id>\d{1,7})', get_distribution),
    url(r'^get_child/', get_child),
)
