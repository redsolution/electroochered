# -*- coding: utf-8 -*-
from django.conf.urls import url
from sadiki.distribution.views import DistributionInfo, DistributionInit, \
    DistributionEnd, DecisionManager, DistributionResults, EndedDistributions, DistributionPlacesResults

urlpatterns = [
#    Работа с комплектованием
    url(r'^$',
        DistributionInfo.as_view(), name='distribution_info'),
    url(r'^ended_distributions/$',
        EndedDistributions.as_view(), name='ended_distributions'),
    url(r'^results/(?P<distribution_id>\d{1,7})/$',
        DistributionResults.as_view(), name='distribution_results'),
    url(r'^places_results/(?P<distribution_id>\d{1,7})/$',
        DistributionPlacesResults.as_view(), name='distribution_places_results'),
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
]
