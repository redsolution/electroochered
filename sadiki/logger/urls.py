# -*- coding: utf-8 -*-
from django.conf.urls import url
from sadiki.logger.views import RequestionLogs, AccountLogs, OperatorLogs, \
    AdmPersonsList, LogsByPerson

urlpatterns = [
    url(r'^request/(?P<requestion_id>\d{1,7})/$',
        RequestionLogs.as_view(), name=u'requestion_logs'),
    url(r'^account_logs/$',
        AccountLogs.as_view(), name=u'account_logs'),
    url(r'^operator_logs/(?P<profile_id>\d{1,7})/$',
        OperatorLogs.as_view(), name=u'operator_logs'),
    url(r'adm_persons/$',
        AdmPersonsList.as_view(), name='adm_persons_list'),
    url(r'by_person/(?P<user_id>\d{1,7})/$',
        LogsByPerson.as_view(), name='logs_by_person'),
]
