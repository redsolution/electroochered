# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url

# social_auth
from django.contrib.auth.decorators import login_required
from sadiki.social_auth_custom.views import AccountSocialAuthCleanData, OperatorSocialAuthCleanData, AccountSocialAuthUpdateData, OperatorSocialAuthUpdateData, AccountSocialAuthDisconnect, OperatorSocialAuthDisconnect, AccountSocialAuthDataUpdate, AccountSocialAuthDataRemove
from social_auth.decorators import dsa_view
from social_auth.views import auth, complete

urlpatterns = patterns('',
    url(r'^login/(?P<backend>[^/]+)/$', auth, name='socialauth_begin'),
    url(r'^connect/(?P<backend>[^/]+)/$', login_required(auth), name='socialauth_connect'),
    url(r'^complete/(?P<backend>[^/]+)/$', complete,
        name='socialauth_complete'),

    # disconnection
    url(r'^account_disconnect/(?P<backend>[^/]+)/(?P<association_id>[^/]+)/$',
        dsa_view()(AccountSocialAuthDisconnect.as_view()), name='account_social_auth_disconnect_individual'),
    url(r'^operator_disconnect/(?P<backend>[^/]+)/(?P<association_id>[^/]+)/$',
        dsa_view()(OperatorSocialAuthDisconnect.as_view()), name='operator_social_auth_disconnect_individual'),

    url(r'^clean_data/$',
        AccountSocialAuthCleanData.as_view(), name='account_social_auth_clean_data'),
    url(r'^clean_data/(?P<user_id>\d{1,7})/$',
        OperatorSocialAuthCleanData.as_view(), name='operator_social_auth_clean_data'),
    url(r'^account_update_data/$',
        AccountSocialAuthUpdateData.as_view(), name='account_social_auth_update_data'),
    url(r'^operator_update_data/(?P<user_id>\d{1,7})/$',
        OperatorSocialAuthUpdateData.as_view(), name='operator_social_auth_update_data'),
    url(r'^account_social_data_update/$',
        AccountSocialAuthDataUpdate.as_view(), name='account_social_data_update'),
    url(r'^account_social_data_remove/$',
        AccountSocialAuthDataRemove.as_view(), name='account_social_data_remove'),
)