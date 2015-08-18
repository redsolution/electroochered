# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

# social_auth
from django.contrib.auth.decorators import login_required
from sadiki.social_auth_custom.views import AccountSocialAuthDisconnect,\
    OperatorSocialAuthDisconnect, AccountSocialAuthDataUpdate, AccountSocialAuthDataRemove, custom_complete,\
    LoginAuth, RegistrationAuth, OperatorSocialAuthDataRemove, OperatorSocialAuthDataUpdate
from social_auth.decorators import dsa_view
from social_auth.views import auth, complete

urlpatterns = patterns('',
    url(r'^login/(?P<backend>[^/]+)/login/$', LoginAuth.as_view(), name='socialauth_login_begin'),
    url(r'^login/(?P<backend>[^/]+)/registration/$', RegistrationAuth.as_view(), name='socialauth_registration_begin'),
    url(r'^connect/(?P<backend>[^/]+)/$', login_required(auth), name='socialauth_connect'),
    url(r'^complete/(?P<backend>[^/]+)/$', complete,
        name='socialauth_complete'),
    url(r'^complete/(?P<backend>[^/]+)/(?P<type>[^/]+)/$', custom_complete,
        name='socialauth_complete'),

    # disconnection
    url(r'^account_disconnect/(?P<backend>[^/]+)/(?P<association_id>[^/]+)/$',
        dsa_view()(AccountSocialAuthDisconnect.as_view()), name='account_social_auth_disconnect_individual'),
    url(r'^operator_disconnect/(?P<backend>[^/]+)/(?P<association_id>[^/]+)/$',
        dsa_view()(OperatorSocialAuthDisconnect.as_view()), name='operator_social_auth_disconnect_individual'),

    url(r'^account_social_data_update/$',
        AccountSocialAuthDataUpdate.as_view(), name='account_social_data_update'),
    url(r'^account_social_data_remove/$',
        AccountSocialAuthDataRemove.as_view(), name='account_social_data_remove'),
    url(r'^operator_social_data_update/(?P<user_id>\d{1,7})/$',
        OperatorSocialAuthDataUpdate.as_view(), name='operator_social_data_update'),
    url(r'^operator_social_data_remove/(?P<user_id>\d{1,7})/$',
        OperatorSocialAuthDataRemove.as_view(), name='operator_social_data_remove'),
)
