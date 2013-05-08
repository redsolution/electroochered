# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt

from sadiki.operator.views.requestion import Registration, RequestionSearch, \
    BenefitCategoryChange, BenefitsChange, FrontPage, RequestionInfo, ProfileChange, \
    RequestionChange, PreferredSadiksChange, DocumentsChange, \
    Queue, RequestionStatusChange, SetIdentityDocument, FindProfileForRequestion, \
    EmbedRequestionToProfile, GenerateBlank, RevalidateEmail, GenerateProfilePassword
from sadiki.operator.views.sadik import SadikListWithGroups, SadikGroupChangePlaces, \
    RequestionListEnrollment, SadikInfoChange

if settings.FACILITY_STORE == settings.FACILITY_STORE_YES:
    change_benefits_view = BenefitsChange.as_view()
else:
    change_benefits_view = BenefitCategoryChange.as_view()

urlpatterns = patterns('',
    # Общие функции
    url(r'^$', FrontPage.as_view(), name='operator_frontpage'),
    url(r'^queue/$', Queue.as_view(), name='operator_queue'),
    url(r'^registration/$', Registration.as_view(),
        name=u'operator_registration'),
    url(r'^requestion_search/$', RequestionSearch.as_view(),
        name=u'operator_requestion_search'),
    # url(r'^revalidate_email/(?P<profile_id>\d{1,7})/$',
    #     csrf_exempt(RevalidateEmail.as_view()), name='revalidate_email'),

    # Работа с конкретной заявкой
    url(r'^request/(?P<requestion_id>\d{1,7})/$',
        RequestionInfo.as_view(), name=u'operator_requestion_info'),
    url(r'^request/(?P<requestion_id>\d{1,7})/change_profile/$',
        ProfileChange.as_view(), name=u'operator_profile_change'),
    url(r'^request/(?P<requestion_id>\d{1,7})/benefits/$',
        change_benefits_view, name=u'operator_benefits_change'),
    url(r'^request/(?P<requestion_id>\d{1,7})/edit/$',
        RequestionChange.as_view(), name=u'operator_requestion_change'),
    url(r'^request/(?P<requestion_id>\d{1,7})/sadiks/$',
        PreferredSadiksChange.as_view(), name=u'operator_preferredsadiks_change'),
    url(r'^request/(?P<requestion_id>\d{1,7})/documents/$',
        DocumentsChange.as_view(), name=u'operator_documents_change'),
    url(r'^request/(?P<requestion_id>\d{1,7})/set_identity_document/$',
        SetIdentityDocument.as_view(), name=u'operator_requestion_set_identity_document'),
    url(r'^request/(?P<requestion_id>\d{1,7})/find_profile/$',
        FindProfileForRequestion.as_view(), name=u'find_profile_for_requestion'),
    url(r'^request/(?P<requestion_id>\d{1,7})/embed_to_profile/(?P<profile_id>\d{1,7})/$',
        EmbedRequestionToProfile.as_view(), name=u'embed_requestion_to_profile'),
    # Смена статуса заявки
    url(r'^request/(?P<requestion_id>\d{1,7})/status-(?P<dst_status>\d{1,3})/$',
        RequestionStatusChange.as_view(), name=u'operator_requestion_status_change'),
    url(r'^request/(?P<requestion_id>\d{1,7})/generate_blank/$',
        GenerateBlank.as_view(), name=u'operator_generate_blank'),
    url(r'^request/(?P<requestion_id>\d{1,7})/generate_profile_password/$',
        GenerateProfilePassword.as_view(), name=u'generate_profile_password'),

    # Работа с садиками
    url(r'^dou/$',
        SadikListWithGroups.as_view(), name=u'sadik_list_with_groups'),
    url(r'^dou/(?P<sadik_id>\d{1,7})/change_info/$',
        SadikInfoChange.as_view(), name=u'sadik_info_change'),
    url(r'^dou/(?P<sadik_id>\d{1,7})/places/$',
        SadikGroupChangePlaces.as_view(), name=u'sadikgroup_change_places'),
    url(r'^dou/requests/$',
        RequestionListEnrollment.as_view(), name=u'requestion_list_enroll'),
)
