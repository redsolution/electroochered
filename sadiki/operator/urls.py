# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt
from sadiki.operator.plugins import plugins

from sadiki.operator.views.requestion import FrontPage, RequestionInfo, \
    RequestionAdd, ConfirmEmail, EmailChange ,\
    RequestionStatusChange, SetIdentityDocument, FindProfileForRequestion, \
    EmbedRequestionToProfile, GenerateBlank, GenerateProfilePassword, ChangeRequestionLocation, ProfileInfo, SocialProfilePublic
from sadiki.operator.views.sadik import SadikListWithGroups, SadikGroupChangePlaces, \
    RequestionListEnrollment, SadikInfoChange, DistributedRequestionsForSadik


urlpatterns = patterns('',
    # Общие функции
    url(r'^$', FrontPage.as_view(), name='operator_frontpage'),

    #профиль
    url(r'^profile/(?P<profile_id>\d{1,7})/$',
        ProfileInfo.as_view(), name=u'operator_profile_info'),
    url(r'^profile/(?P<profile_id>\d{1,7})/requestion_add/$',
        RequestionAdd.as_view(), name=u'operator_requestion_add'),
    url(r'^profile/(?P<profile_id>\d{1,7})/generate_profile_password/$',
        GenerateProfilePassword.as_view(), name=u'generate_profile_password'),
    url(r'^social_profile_public/(?P<profile_id>\d{1,7})/$',
        SocialProfilePublic.as_view(), name='operator_social_profile_public'),
    url(r'^profile/(?P<profile_id>\d{1,7})/save_email/$',
        EmailChange.as_view(), name=u'change_profile_email'),
    url(r'^profile/(?P<profile_id>\d{1,7})/confirm_email/$',
        ConfirmEmail.as_view(), name=u'confirm_profile_email'),

    # Работа с конкретной заявкой
    url(r'^request/(?P<requestion_id>\d{1,7})/$',
        RequestionInfo.as_view(), name=u'operator_requestion_info'),
    url(r'^request/(?P<requestion_id>\d{1,7})/set_identity_document/$',
        SetIdentityDocument.as_view(), name=u'operator_requestion_set_identity_document'),
    url(r'^request/(?P<requestion_id>\d{1,7})/find_profile/$',
        FindProfileForRequestion.as_view(), name=u'find_profile_for_requestion'),
    url(r'^request/(?P<requestion_id>\d{1,7})/embed_to_profile/(?P<profile_id>\d{1,7})/$',
        EmbedRequestionToProfile.as_view(), name=u'embed_requestion_to_profile'),
    url(r'^request/(?P<requestion_id>\d{1,7})/change_location/$',
        ChangeRequestionLocation.as_view(), name=u'change_requestion_location'),
    # Смена статуса заявки
    url(r'^request/(?P<requestion_id>\d{1,7})/status-(?P<dst_status>\d{1,3})/$',
        RequestionStatusChange.as_view(), name=u'operator_requestion_status_change'),
    url(r'^request/(?P<requestion_id>\d{1,7})/generate_blank/$',
        GenerateBlank.as_view(), name=u'operator_generate_blank'),

    # Работа с садиками
    url(r'^dou/$',
        SadikListWithGroups.as_view(), name=u'sadik_list_with_groups'),
    url(r'^dou/(?P<sadik_id>\d{1,7})/change_info/$',
        SadikInfoChange.as_view(), name=u'sadik_info_change'),
    url(r'^dou/(?P<sadik_id>\d{1,7})/places/$',
        SadikGroupChangePlaces.as_view(), name=u'sadikgroup_change_places'),
    url(r'^dou/(?:(?P<sadik_id>\d{1,7})/)?requests/$',
        RequestionListEnrollment.as_view(), name=u'requestion_list_enroll'),
    url(r'^dou/(?P<sadik_id>\d{1,7})/distributed_requestions/$',
        DistributedRequestionsForSadik.as_view(), name=u'distributed_requestions_for_sadik'),
)

for plugin in plugins:
    try:
        urlpatterns += plugin.get_urls()
    except NotImplementedError:
        pass
