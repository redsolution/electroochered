# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url
from sadiki.logger.views import RequestionLogs, AccountLogs, OperatorLogs

urlpatterns = patterns('',
    url(r'^request/(?P<requestion_id>\d{1,7})/$',
        RequestionLogs.as_view(), name=u'requestion_logs'),
    url(r'^account_logs/$',
        AccountLogs.as_view(), name=u'account_logs'),
    url(r'^operator_logs/(?P<profile_id>\d{1,7})/$',
        OperatorLogs.as_view(), name=u'operator_logs'),
)
