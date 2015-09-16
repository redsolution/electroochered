# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url, include

# social_auth
from django.contrib.auth.decorators import login_required
from sadiki.social_auth_custom.views import AccountSocialAuthDisconnect,\
    OperatorSocialAuthDisconnect, AccountSocialAuthDataUpdate, AccountSocialAuthDataRemove, custom_complete,\
    LoginAuth, OperatorSocialAuthDataRemove, OperatorSocialAuthDataUpdate
from social.apps.django_app.utils import psa
from social.apps.django_app.views import auth, complete

urlpatterns = patterns('',
    url(r'^login/(?P<backend>[^/]+)/$', auth, name='login'),
    url(r'^connect/(?P<backend>[^/]+)/$', login_required(auth), name='connect'),
    url(r'^complete/(?P<backend>[^/]+)/$', complete,
        name='complete'),
    url(r'^account_disconnect/(?P<backend>[^/]+)/(?P<association_id>[^/]+)/$',
        AccountSocialAuthDisconnect.as_view(), name='account_disconnect_individual'),
    url(r'^operator_disconnect/(?P<backend>[^/]+)/(?P<association_id>[^/]+)/$',
        OperatorSocialAuthDisconnect.as_view(), name='operator_disconnect_individual'),

    url(r'^account_social_data_update/$',
        AccountSocialAuthDataUpdate.as_view(), name='account_social_data_update'),
    url(r'^account_social_data_remove/$',
        AccountSocialAuthDataRemove.as_view(), name='account_social_data_remove'),
    url(r'^operator_social_data_update/(?P<user_id>\d{1,7})/$',
        OperatorSocialAuthDataUpdate.as_view(), name='operator_social_data_update'),
    url(r'^operator_social_data_remove/(?P<user_id>\d{1,7})/$',
        OperatorSocialAuthDataRemove.as_view(), name='operator_social_data_remove'),
)
