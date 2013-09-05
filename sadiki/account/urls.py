# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls.defaults import patterns, url
from sadiki.account.views import RequestionAdd, \
    AccountFrontPage, RequestionInfo, GenerateBlank, SocialProfilePublic, AccountPGUDataRemove

urlpatterns = patterns('',
    url(r'^$', AccountFrontPage.as_view(), name='account_frontpage'),
    url(r'^request/add/$', RequestionAdd.as_view(),
        name=u'requestion_add_by_user'),
    url(r'^request/(?P<requestion_id>\d{1,7})/$',
        RequestionInfo.as_view(), name=u'account_requestion_info'),
    url(r'^request/(?P<requestion_id>\d{1,7})/generate_blank/$',
        GenerateBlank.as_view(), name='account_generate_blank'),
    url(r'^social_profile_public/$',
        SocialProfilePublic.as_view(), name='social_profile_public'),
    url(r'^account_pgu_data_remove/$',
        AccountPGUDataRemove.as_view(), name='account_pgu_data_remove'),
)
