# -*- coding: utf-8 -*- 
from django.conf.urls import patterns, url
from sadiki.supervisor.views import FrontPage, ChangeRegistrationDateTime, \
    ChangeBirthDate, RequestionSearch, \
    RequestionInfo, StartDistributionYear, DistributionYearInfo, RequestionStatusChange

urlpatterns = patterns('',
    url(r'^$', FrontPage.as_view(), name='supervisor_frontpage'),
    url(r'^requestion_info/(?P<requestion_id>\d{1,7})/$',
        RequestionInfo.as_view(), name=u'supervisor_requestion_info'),
    url(r'^change_registration_datetime/(?P<requestion_id>\d{1,7})/$',
        ChangeRegistrationDateTime.as_view(),
        name=u'change_registration_datetime'),
    url(r'^change_birth_date/(?P<requestion_id>\d{1,7})/$',
        ChangeBirthDate.as_view(), name=u'change_birth_date'),
    url(r'^distribution_year_info/$',
        DistributionYearInfo.as_view(), name=u'distribution_year_info'),
    url(r'^start_distribution_year/$',
        StartDistributionYear.as_view(), name=u'start_distribution_year'),
    url(r'^request/(?P<requestion_id>\d{1,7})/status-(?P<dst_status>\d{1,3})/$',
        RequestionStatusChange.as_view(), name=u'supervisor_requestion_status_change'),
)
