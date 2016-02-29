# -*- coding: utf-8 -*-
from django.conf.urls import url
from sadiki.statistics.views import DistributionStatistics, DecisionStatistics, \
    WaitTimeStatistics

urlpatterns = [
    # url('^decision_statistics/(?:(?P<year>\d{4})/)?$',
    #     DecisionStatistics.as_view(), name='decision_statistics'),
    # url('^distribution_statistics/(?:(?P<year>\d{4})/)?$',
    #     DistributionStatistics.as_view(), name='distribution_statistics'),
    url('^wait_time_statistics/$', WaitTimeStatistics.as_view(),
        name='wait_time_statistics'),
]
