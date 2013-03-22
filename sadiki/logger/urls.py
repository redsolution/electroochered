# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url
from sadiki.logger.views import RequestionLogs, Reports, ReportsForType, \
    ReportShow, RequestionLogsForAccount, RequestionLogsForOperator

urlpatterns = patterns('',
    url(r'^request/(?P<requestion_id>\d{1,7})/$',
        RequestionLogs.as_view(), name=u'requestion_logs'),
    url(r'^account/request/(?P<requestion_id>\d{1,7})/$',
        RequestionLogsForAccount.as_view(), name=u'requestion_logs_for_account'),
    url(r'^operator/request/(?P<requestion_id>\d{1,7})/$',
        RequestionLogsForOperator.as_view(),
        name=u'requestion_logs_for_operator'),

    url(r'^reports/$', Reports.as_view(), name=u'reports'),
    url(r'^reports/by-type/(?P<report_type>\d{1,7})/$',
        ReportsForType.as_view(), name=u'reports_for_type'),
    url(r'^reports/(?P<report_id>\d{1,7})/$',
        ReportShow.as_view(), name=u'show_report'),
)
