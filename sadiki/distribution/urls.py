# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url
from sadiki.distribution.views import DistributionInfo, DistributionInit, \
    DistributionEnd, DecisionManager

urlpatterns = patterns('',
#    Работа с комплектованием
    url(r'^(?:results/(?P<distribution_id>\d{1,7})/)?$',
        DistributionInfo.as_view(), name='distribution_info'),
    url(r'^new/$',
        DistributionInit.as_view(), name='distribution_init'),
    url(r'^decision_manager/$',
        DecisionManager.as_view(), name='decision_manager'),
#    url(r'^progress/$',
#        DistributionProgress.as_view(), name='distribution_progress'),
#    url(r'^autorun/$',
#        RunAutomaticDistribution.as_view(), name='distribution_autorun'),
#    url(r'^swap/(?:(?P<requestion_id>\d{1,7})/)?$',
#        DistributionEditmanually.as_view(), name='distribution_swap_requestions'),
    url(r'^finish/$',
        DistributionEnd.as_view(), name='distribution_end'),
)
