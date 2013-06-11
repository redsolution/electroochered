# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url
from sadiki.logger.views import RequestionLogs, RequestionLogsForAccount, RequestionLogsForOperator

urlpatterns = patterns('',
    url(r'^request/(?P<requestion_id>\d{1,7})/$',
        RequestionLogs.as_view(), name=u'requestion_logs'),
    url(r'^account/request/(?P<requestion_id>\d{1,7})/$',
        RequestionLogsForAccount.as_view(), name=u'requestion_logs_for_account'),
    url(r'^operator/request/(?P<requestion_id>\d{1,7})/$',
        RequestionLogsForOperator.as_view(),
        name=u'requestion_logs_for_operator'),
)
